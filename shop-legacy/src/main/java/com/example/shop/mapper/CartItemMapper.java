package com.example.shop.mapper;

import com.example.shop.domain.CartItem;

import java.util.List;
import java.util.Map;

public interface CartItemMapper {

    void insert(CartItem cartItem);

    List<CartItem> selectByCartId(Long cartId);

    CartItem selectById(Long id);

    void updateQuantity(Map<String, Object> params);

    void deleteById(Long id);

    void deleteByCartId(Long cartId);

    int countByCartId(Long cartId);
}
