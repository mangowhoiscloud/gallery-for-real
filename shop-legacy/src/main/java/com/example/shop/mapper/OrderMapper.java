package com.example.shop.mapper;

import com.example.shop.domain.Order;

import java.util.List;
import java.util.Map;

public interface OrderMapper {

    void insert(Order order);

    Order selectById(Long id);

    List<Order> selectByMemberId(Map<String, Object> params);

    List<Order> selectAll(Map<String, Object> params);

    void updateStatus(Map<String, Object> params);

    int countByMemberId(Long memberId);

    int countAll();

    int countActiveByMemberId(Long memberId);

    List<Order> selectPendingByMemberId(Long memberId);

    void deleteByMemberId(Long memberId);
}
