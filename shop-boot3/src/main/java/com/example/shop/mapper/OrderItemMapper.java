package com.example.shop.mapper;

import com.example.shop.dto.OrderItemResponse;
import com.example.shop.entity.OrderItem;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface OrderItemMapper {

    void insertOrderItem(OrderItem item);

    List<OrderItemResponse> findByOrderId(Long orderId);
}
