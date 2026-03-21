package com.example.shop.mapper;

import com.example.shop.entity.Cart;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface CartMapper {

    void insertCart(Cart cart);

    Cart findByMemberId(Long memberId);
}
