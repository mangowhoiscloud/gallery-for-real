package com.example.shop.dto;

import com.example.shop.entity.Member;
import com.example.shop.entity.MemberRole;

import java.time.LocalDateTime;

public record MemberResponse(
        Long id,
        String email,
        String name,
        String phone,
        String address,
        MemberRole role,
        Boolean active,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {
    public static MemberResponse from(Member member) {
        return new MemberResponse(
                member.getId(),
                member.getEmail(),
                member.getName(),
                member.getPhone(),
                member.getAddress(),
                member.getRole(),
                member.getActive(),
                member.getCreatedAt(),
                member.getUpdatedAt()
        );
    }
}
