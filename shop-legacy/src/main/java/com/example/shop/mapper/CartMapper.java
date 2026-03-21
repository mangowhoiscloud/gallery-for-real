package com.example.shop.mapper;

import com.example.shop.domain.Cart;

public interface CartMapper {

    void insert(Cart cart);

    Cart selectByMemberId(Long memberId);

    void delete(Long id);
}
