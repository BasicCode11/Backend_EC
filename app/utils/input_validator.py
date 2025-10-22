import re
import html
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from fastapi import HTTPException, status

class InputValidationError(Exception):
    """Custom exception for input validation errors."""
    pass
