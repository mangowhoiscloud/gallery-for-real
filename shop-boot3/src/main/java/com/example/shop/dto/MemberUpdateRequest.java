package com.example.shop.dto;

import jakarta.validation.constraints.Size;

public record MemberUpdateRequest(
        @Size(max = 50) String name,
        @Size(min = 10, max = 15) String phone,
        @Size(max = 200) String address
) {}
