package com.example.shop.dto;

import java.util.List;

public record MemberPageResponse(
        List<MemberResponse> content,
        int totalPages,
        long totalElements,
        int currentPage,
        int pageSize
) {}
