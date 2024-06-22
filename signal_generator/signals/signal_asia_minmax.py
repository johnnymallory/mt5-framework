from datetime import datetime, time

import MetaTrader5 as mt5

from events.events import DataEvent, SignalEvent, UpdateEvent
from data_provider.data_provider import DataProvider
from ..interfaces.signal_generator_interface import ISignalGenerator
from ..properties.signal_generator_properties import AsiaMinMaxProps
from portfolio.portfolio import Portfolio
from order_executor.order_executor import OrderExecutor

class SignalAsiaMinMax(ISignalGenerator):
    
    def __init__(self, properties: AsiaMinMaxProps):
        """
        Initializes the AsiaMinMax object.

        Args:
            properties (AsiaMinMaxProps): The properties object containing the parameters for Asia min max area strategy.
        """
        # The pips of the Stop Loss
        if properties.sl_pips > 0:
            self.sl_pips = properties.sl_pips
        else:
            self.sl_pips = 0
            
        # The timeframe of the bars
        self.timeframe = properties.timeframe
        self.last_trade_date = None
        
        # Ints that define the begining and end of the reference area (E.g. 10:30 should be hours = 10, mins = 30)
        self.reference_area_start_hour = properties.reference_area_start_hour
        self.reference_area_start_min = properties.reference_area_end_min
        self.reference_area_end_hour = properties.reference_area_end_hour
        self.reference_area_end_min = properties.reference_area_end_min
        
        # Ints that define the begining and end of the operational trading area (E.g. 10:30 should be hours = 10, mins = 30)
        self.operational_area_start_hour = properties.operational_area_start_hour
        self.operational_area_start_min = properties.operational_area_start_min
        self.operational_area_end_hour = properties.operational_area_end_hour
        self.operational_area_end_min = properties.operational_area_end_min              
        
    def _update_trailing_stop(self, position, last_tick, tp_price, entry_price):
        profit_range = abs(tp_price - entry_price)
        current_price = last_tick['bid'] if position.type == mt5.ORDER_TYPE_BUY else last_tick['ask']
        price_movement = abs(current_price - entry_price)
        
        # Si el precio ha alcanzado el 50% del rango hacia el TP
        if price_movement >= profit_range * 0.5:
            # Primero, movemos el SL a break even
            new_sl = entry_price
            
            # Si el precio ha superado el 50% del rango, aplicamos el trailing stop
            if price_movement > profit_range * 0.5:
                # Calculamos la distancia que el precio se ha movido más allá del 50%
                extra_movement = price_movement - (profit_range * 0.5)
                # El trailing stop se mueve al 50% de este movimiento extra
                trailing_distance = extra_movement * 0.5
                
                if position.type == mt5.ORDER_TYPE_BUY:
                    new_sl = max(new_sl, current_price - trailing_distance)
                else:
                    new_sl = min(new_sl, current_price + trailing_distance)
                
                # Aseguramos que el SL no supere el 30% del rango cuando el precio alcance el 80%
                max_sl_movement = profit_range * 0.3
                if position.type == mt5.ORDER_TYPE_BUY:
                    new_sl = min(new_sl, entry_price + max_sl_movement)
                else:
                    new_sl = max(new_sl, entry_price - max_sl_movement)
            
            return new_sl
        
        return None
    
    def generate_signal(self, data_event: DataEvent, data_provider: DataProvider, portfolio: Portfolio, order_executor: OrderExecutor) -> SignalEvent | None:
        """
        Generates a signal based on the Asia Min Max strategy.

        Args:
            data_event (DataEvent): The data event that triggered the signal generation.
            data_provider (DataProvider): The data provider used to retrieve the necessary data.
            portfolio (Portfolio): The portfolio containing the open positions.
            order_executor (OrderExecutor): The order executor used to execute the orders.

        Returns:
            SignalEvent | None: The generated signal event or None if no signal.
        """
        symbol = data_event.symbol
        today = datetime.now().date()
        current_time = datetime.now().time()
        
        # Si ya hemos operado hoy, no generamos nuevas señales de entrada
        if self.last_trade_date == today:
            return None
        
        # Calculate reference area
        reference_area_start = datetime.combine(today, self.reference_area_start)
        reference_area_end = datetime.combine(today, self.reference_area_end)
        
        reference_area_bars = data_provider.get_bars_from_range(symbol=symbol,
                                                                timeframe=self.timeframe,
                                                                start_date=reference_area_start,
                                                                end_date=reference_area_end)
        
        # Handle fail to retrieve data
        if reference_area_bars is None:
            self.logger.error(f"Error: No se han podido obtener los datos del símbolo {symbol}.")
            return None
        
        reference_area_max_price = reference_area_bars['high'].max()
        reference_area_min_price = reference_area_bars['low'].min()
        
        # Get the open positions of the account
        symbol_open_positions = portfolio.get_number_of_strategy_open_positions_by_symbol(symbol)
        
        signal = ""
        sl_price = 0
        tp_price = 0
        
        # If we are inside the operational area timeframe and we don't have any open position
        if self.operational_area_start <= current_time <= self.operational_area_end and symbol_open_positions == 0:
            last_price = data_provider.get_latest_closed_bar(symbol, self.timeframe)['close']
            last_tick = data_provider.get_latest_tick(symbol)
            points = mt5.symbol_info(symbol).point
            
            # SELL Signal
            if last_price > reference_area_max_price:
                signal = "SELL"
                tp_price = reference_area_min_price
                sl_price = last_tick['bid'] + self.sl_pips * points if self.sl_pips > 0 else 0
            
            # BUY Signal
            elif last_price < reference_area_min_price:
                signal = "BUY"
                tp_price = reference_area_max_price
                sl_price = last_tick['ask'] - self.sl_pips * points if self.sl_pips > 0 else 0
        
        # Implementar trailing stop
        positions = portfolio.get_open_positions()
        last_tick = data_provider.get_latest_tick(symbol)
        
        for position in positions:
            if position.symbol == symbol:
                new_sl = self._update_trailing_stop(position, last_tick, position.tp, position.price_open)
                
                if new_sl is not None and new_sl != position.sl:
                    return UpdateEvent(symbol=symbol,
                                        signal="UPDATE",
                                        target_order="UPDATE",
                                        magic_number=position.magic,
                                        ticket=position.ticket,
                                        sl=new_sl,
                                        tp=position.tp)
        
        if signal:
            self.last_trade_date = today
            return SignalEvent(symbol=symbol,
                                signal=signal,
                                target_order="MARKET",
                                target_price=0.0,
                                magic_number=portfolio.magic,
                                sl=sl_price,
                                tp=tp_price)
        
        return None