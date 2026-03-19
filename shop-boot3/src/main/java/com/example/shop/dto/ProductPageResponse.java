package com.example.shop.dto;

import java.util.List;

public record ProductPageResponse(
        List<ProductResponse> content,
        int totalPages,
        long totalElements,
        int currentPage,
        int pageSize
) {}
