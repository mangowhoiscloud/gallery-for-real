package com.example.shop.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record OrderCreateRequest(
        @NotBlank @Size(max = 200) String shippingAddress
) {}
