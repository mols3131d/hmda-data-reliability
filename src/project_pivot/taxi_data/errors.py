"""Taxi 데이터 파운데이션 예외."""


class TaxiDataFoundationError(Exception):
    """Taxi 데이터 파운데이션 기본 예외."""


class TaxiDataLoadError(TaxiDataFoundationError):
    """원천 데이터 적재에 실패했다."""


class SyntheticCaseError(TaxiDataFoundationError):
    """합성 결함 데이터 생성에 실패했다."""
