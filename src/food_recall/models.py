"""数据模型定义"""

from typing import List, Optional
from pydantic import BaseModel


class ComboItem(BaseModel):
    """单品信息"""
    name: str
    qty: int = 1


class Combo(BaseModel):
    """套餐信息"""
    combo_id: int
    combo_name: str
    items: List[ComboItem]
    tags: List[str]
    calories: int
    sales_volume: int = 0


class Demand(BaseModel):
    """单条需求"""
    demand_id: int
    content: str


class ValidationResult(BaseModel):
    """单条需求的核验结果"""
    demand_id: int
    demand: str
    match: bool
    reason: str


class ComboValidation(BaseModel):
    """单个套餐的核验结果"""
    combo_id: int
    combo_name: str
    score: int
    total_demands: int
    results: List[ValidationResult]
    unmet_reasons: List[str] = []


class CalorieExtraction(BaseModel):
    """热量提取结果"""
    target_calorie: Optional[int] = None


class DemandExtraction(BaseModel):
    """需求提取结果"""
    demands: List[Demand]
    total: int


class CalorieRange(BaseModel):
    """热量范围"""
    lower_bound: int
    upper_bound: int


class ValidationSummary(BaseModel):
    """核验汇总"""
    perfect_match_count: int = 0
    partial_match_count: int = 0
    no_match_count: int = 0


class RouteDecision(BaseModel):
    """路由决策"""
    route: str  # "perfect_match" | "fallback" | "no_match"