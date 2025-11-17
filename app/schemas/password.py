"""
Password reset schemas for forgot/reset password flow.
"""
from pydantic import BaseModel, EmailStr, Field


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr = Field(..., description="User's registered email address")


class ForgotPasswordResponse(BaseModel):
    """Schema for forgot password response"""
    message: str = Field(default="If the email exists, a password reset link has been sent")


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request"""
    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")
    confirm_password: str = Field(..., description="Confirm new password")


class ResetPasswordResponse(BaseModel):
    """Schema for reset password response"""
    message: str = Field(default="Password has been reset successfully")


class ChangePasswordRequest(BaseModel):
    """Schema for authenticated user changing their password"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")


class ChangePasswordResponse(BaseModel):
    """Schema for change password response"""
    message: str = Field(default="Password changed successfully")

