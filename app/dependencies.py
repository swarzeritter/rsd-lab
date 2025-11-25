from fastapi import Depends, HTTPException, status
from typing import Optional


# Приклад залежностей, які можна використовувати в роутерах
def get_common_query_params(
    skip: int = 0,
    limit: int = 100
):
    """
    Загальні query параметри для пагінації
    """
    if limit > 100:
        limit = 100
    return {"skip": skip, "limit": limit}

