from pydantic import BaseModel

class BaseSignalProps(BaseModel):
    pass

class MACrossoverProps(BaseSignalProps):
    """
    Represents the properties for a Moving Average Crossover signal generator.

    Attributes:
        timeframe (str): The timeframe for the signal generator.
        fast_period (int): The period for the fast moving average.
        slow_period (int): The period for the slow moving average.
    """
    timeframe: str
    fast_period: int
    slow_period: int

class RSIProps(BaseSignalProps):
    """
    Represents the properties for a RSI Mean Reverse signal generator.

    Attributes:
        timeframe (str): The timeframe for the signal generator.
        rsi_period (int): The period for the RSI indicator
        rsi_upper (float): The upper band of the RSI indicator
        rsi_lower (float): The lower band of the RSI indicator
        sl_points (int): The number of pips of the Stop Loss
        tp_points (int): The numer of pips of the Take Profit
    """
    timeframe: str
    rsi_period: int
    rsi_upper: float
    rsi_lower: float
    sl_points: int
    tp_points: int
    
class AsiaMinMaxProps(BaseSignalProps):
    """
    Represents the properties for Asia MinMax signal generator.
    
    Attributes:
        timeframe (str): The timeframe for the signal generator
        reference_area_start_hour (int): The hour strategy will start looking for reference area
        reference_area_start_min (int): The min strategy will start looking for reference area
        reference_area_end_hour (int): The hour strategy will end looking for reference area
        reference_area_end_min (int): The min strategy will end looking for reference area
        operational_area_start_hour (int): The start hour of the area for trading
        operational-area_start_min (int): The start min of the area for trading
        operational_area_end_hour (int): The end hour of the area for trading
        operational_area_end_min (int): The end min of the area for trading
        sl_pips (int): Number of pips of the Stop Loss
    """
    timeframe: str
    reference_area_start_hour: int
    reference_area_start_min: int
    reference_area_end_hour: int
    reference_area_end_min: int
    operational_area_start_hour: int
    operational_area_start_min: int
    operational_area_end_hour: int
    operational_area_end_min: int
    sl_pips: int