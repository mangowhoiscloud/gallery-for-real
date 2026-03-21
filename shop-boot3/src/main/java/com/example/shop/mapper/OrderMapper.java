package com.example.shop.mapper;

import com.example.shop.dto.OrderResponse;
import com.example.shop.entity.Order;
import com.example.shop.entity.OrderStatus;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface OrderMapper {

    void insertOrder(Order order);

    List<Order> findByMemberId(
            @Param("memberId") Long memberId,
            @Param("offset") int offset,
            @Param("limit") int limit);

    int countByMemberId(Long memberId);

    OrderResponse findById(Long id);

    void updateStatus(@Param("id") Long id, @Param("status") OrderStatus status);

    List<Order> findAll(
            @Param("status") String status,
            @Param("offset") int offset,
            @Param("limit") int limit);

    int countAll(@Param("status") String status);
}
