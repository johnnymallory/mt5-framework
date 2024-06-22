from pydantic import BaseModel

class BaseRiskProps(BaseModel):
    pass

class MaxLeverageFactorRiskProps(BaseRiskProps):
    """
    Risk properties for managing maximum leverage factor.
    """

    max_leverage_factor: float