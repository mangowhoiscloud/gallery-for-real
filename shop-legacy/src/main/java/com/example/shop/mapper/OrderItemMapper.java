package com.example.shop.mapper;

import com.example.shop.domain.OrderItem;

import java.util.List;

public interface OrderItemMapper {

    void insertBatch(List<OrderItem> items);

    List<OrderItem> selectByOrderId(Long orderId);
}
