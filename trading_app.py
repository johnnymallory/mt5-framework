from platform_connector.platform_connector import PlatformConnector
from data_provider.data_provider import DataProvider
from trading_director.trading_director import TradingDirector
from signal_generator.signal_generator import SignalGenerator
from signal_generator.properties.signal_generator_properties import MACrossoverProps, RSIProps, AsiaMinMaxProps
from position_sizer.position_sizer import PositionSizer
from position_sizer.properties.position_sizer_properties import MinSizingProps, FixedSizingProps, RiskPctSizingProps
from portfolio.portfolio import Portfolio
from risk_manager.risk_manager import RiskManager
from risk_manager.properties.risk_manager_properties import MaxLeverageFactorRiskProps
from order_executor.order_executor import OrderExecutor
from notifications.notifications import NotificationService, TelegramNotificationProperties
from queue import Queue
from dotenv import load_dotenv, find_dotenv
import os

if __name__ == "__main__":
    

    # Definición de variables necesarias para la estrategia
    symbols = ['EURUSD', 'GBPJPY', 'XAUUSD', 'GBPUSD']
    timeframe = '5min'
    magic_number = 12345

    mac_props = MACrossoverProps(timeframe=timeframe,
                                fast_period=5,
                                slow_period=10)
    
    rsi_props = RSIProps(timeframe=timeframe,
                        rsi_period=5,
                        rsi_upper=70.0,
                        rsi_lower=30.0,
                        sl_points=50,
                        tp_points=100)
    
    asia_minmax_props = AsiaMinMaxProps(timeframe=timeframe,
                                        reference_area_start_hour=0,
                                        reference_area_start_min=0,
                                        reference_area_end_hour=8,
                                        reference_area_end_min=0,
                                        operational_area_start_hour=8,
                                        operational_area_start_min=50,
                                        operational_area_end_hour=10,
                                        operational_area_end_min=30,
                                        sl_pips=5)

    # Creación de la cola de eventos principal
    events_queue = Queue()
    
    # Creación de los módulos principales del Framework
    CONNECT = PlatformConnector(symbol_list=symbols)
    
    DATA_PROVIDER = DataProvider(events_queue=events_queue,
                                symbol_list=symbols,
                                timeframe=timeframe)
    
    PORTFOLIO = Portfolio(magic_number=magic_number)

    ORDER_EXECUTOR = OrderExecutor(events_queue=events_queue,
                                    portfolio=PORTFOLIO)

    SIGNAL_GENERATOR = SignalGenerator(events_queue=events_queue,
                                        data_provider=DATA_PROVIDER,
                                        portfolio=PORTFOLIO,
                                        order_executor=ORDER_EXECUTOR,
                                        signal_properties=asia_minmax_props)
    
    POSITION_SIZER = PositionSizer(events_queue=events_queue,
                                    data_provider=DATA_PROVIDER,
                                    sizing_properties=FixedSizingProps(volume=0.01))


    RISK_MANAGER = RiskManager(events_queue=events_queue,
                                data_provider=DATA_PROVIDER,
                                portfolio=PORTFOLIO,
                                risk_properties=MaxLeverageFactorRiskProps(max_leverage_factor=5))
    
    # Buscamos el archivo .env y cargamos sus valores
    load_dotenv(find_dotenv())
    
    NOTIFICATIONS = NotificationService(
        properties=TelegramNotificationProperties(
            token=os.getenv("TELEGRAM_TOKEN"),
            chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        )
    )   


    # Creación del trading director y ejecución del método principal
    TRADING_DIRECTOR = TradingDirector(events_queue=events_queue,
                                        data_provider=DATA_PROVIDER,
                                        signal_generator=SIGNAL_GENERATOR,
                                        position_sizer=POSITION_SIZER,
                                        risk_manager=RISK_MANAGER,
                                        order_executor=ORDER_EXECUTOR,
                                        notification_service=NOTIFICATIONS)
    
    TRADING_DIRECTOR.execute()