package com.example.shop.mapper;

import com.example.shop.dto.OrderResponse;
import com.example.shop.entity.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
@Transactional
class OrderMapperTest {

    @Autowired OrderMapper     orderMapper;
    @Autowired OrderItemMapper orderItemMapper;
    @Autowired MemberMapper    memberMapper;
    @Autowired ProductMapper   productMapper;

    private Member  member;
    private Product product;

    @BeforeEach
    void setUp() {
        member = new Member();
        member.setEmail("order-test@example.com");
        member.setPassword("hashed");
        member.setName("Order Tester");
        member.setPhone("01011112222");
        member.setAddress("Seoul");
        member.setRole(MemberRole.USER);
        member.setActive(true);
        memberMapper.insert(member);

        product = new Product();
        product.setName("Test Product");
        product.setDescription("For order FK");
        product.setPrice(new BigDecimal("29.99"));
        product.setStockQuantity(100);
        product.setCategory("Test");
        product.setImageUrl("https://example.com/img/test.jpg");
        product.setStatus(ProductStatus.ACTIVE);
        productMapper.insert(product);
    }

    private Order buildOrder(String address, BigDecimal total) {
        Order o = new Order();
        o.setMemberId(member.getId());
        o.setTotalAmount(total);
        o.setStatus(OrderStatus.PENDING);
        o.setShippingAddress(address);
        return o;
    }

    private OrderItem buildItem(Long orderId, String name, int qty, BigDecimal price) {
        OrderItem oi = new OrderItem();
        oi.setOrderId(orderId);
        oi.setProductId(product.getId());
        oi.setProductName(name);
        oi.setQuantity(qty);
        oi.setUnitPrice(price);
        return oi;
    }

    @Test
    void insertOrder_andFindByMemberId() {
        Order order = buildOrder("123 Main St", new BigDecimal("59.99"));
        orderMapper.insertOrder(order);

        assertThat(order.getId()).isNotNull();

        List<Order> orders = orderMapper.findByMemberId(member.getId(), 0, 10);
        assertThat(orders).hasSize(1);

        Order found = orders.get(0);
        assertThat(found.getMemberId()).isEqualTo(member.getId());
        assertThat(found.getTotalAmount()).isEqualByComparingTo(new BigDecimal("59.99"));
        assertThat(found.getStatus()).isEqualTo(OrderStatus.PENDING);
        assertThat(found.getShippingAddress()).isEqualTo("123 Main St");
        assertThat(found.getCreatedAt()).isNotNull();
        assertThat(found.getUpdatedAt()).isNotNull();
    }

    @Test
    void findById_withNoItems_returnsEmptyItemList() {
        Order order = buildOrder("456 Oak Ave", new BigDecimal("149.97"));
        orderMapper.insertOrder(order);

        OrderResponse resp = orderMapper.findById(order.getId());
        assertThat(resp).isNotNull();
        assertThat(resp.getId()).isEqualTo(order.getId());
        assertThat(resp.getMemberId()).isEqualTo(member.getId());
        assertThat(resp.getTotalAmount()).isEqualByComparingTo(new BigDecimal("149.97"));
        assertThat(resp.getStatus()).isEqualTo(OrderStatus.PENDING);
        assertThat(resp.getShippingAddress()).isEqualTo("456 Oak Ave");
        assertThat(resp.getCreatedAt()).isNotNull();
        assertThat(resp.getItems()).isNotNull();
        assertThat(resp.getItems()).isEmpty();
    }

    @Test
    void findById_withItemsJoined_returnsPopulatedItemList() {
        Order order = buildOrder("789 Elm Rd", new BigDecimal("99.98"));
        orderMapper.insertOrder(order);

        // Snapshot names differ from product.name to verify snapshot behaviour
        OrderItem item1 = buildItem(order.getId(), "Gadget Pro", 2, new BigDecimal("29.99"));
        OrderItem item2 = buildItem(order.getId(), "Widget Max", 1, new BigDecimal("39.99"));
        orderItemMapper.insertOrderItem(item1);
        orderItemMapper.insertOrderItem(item2);

        OrderResponse resp = orderMapper.findById(order.getId());
        assertThat(resp.getItems()).hasSize(2);
        assertThat(resp.getItems()).anyMatch(i -> i.productName().equals("Gadget Pro") && i.quantity() == 2);
        assertThat(resp.getItems()).anyMatch(i -> i.productName().equals("Widget Max") && i.quantity() == 1);
        assertThat(resp.getItems()).allMatch(i -> i.orderId().equals(order.getId()));
    }

    @Test
    void updateStatus_changesStatusField() {
        Order order = buildOrder("321 Pine Blvd", new BigDecimal("20.00"));
        orderMapper.insertOrder(order);

        orderMapper.updateStatus(order.getId(), OrderStatus.CONFIRMED);

        List<Order> orders = orderMapper.findByMemberId(member.getId(), 0, 10);
        assertThat(orders).hasSize(1);
        assertThat(orders.get(0).getStatus()).isEqualTo(OrderStatus.CONFIRMED);
    }

    @Test
    void findAll_withAndWithoutStatusFilter() {
        Order pending = buildOrder("Address A", new BigDecimal("10.00"));
        Order confirmed = buildOrder("Address B", new BigDecimal("20.00"));
        confirmed.setStatus(OrderStatus.CONFIRMED);
        orderMapper.insertOrder(pending);
        orderMapper.insertOrder(confirmed);

        // No filter: all orders for this member visible
        List<Order> all = orderMapper.findAll(null, 0, 100);
        assertThat(all.stream().filter(o -> o.getMemberId().equals(member.getId()))).hasSize(2);

        // Filter by PENDING: only PENDING orders returned
        List<Order> pendingList = orderMapper.findAll("PENDING", 0, 100);
        assertThat(pendingList).allMatch(o -> o.getStatus() == OrderStatus.PENDING);
        assertThat(pendingList).anyMatch(o -> o.getId().equals(pending.getId()));

        // Filter by CONFIRMED: only CONFIRMED orders returned
        List<Order> confirmedList = orderMapper.findAll("CONFIRMED", 0, 100);
        assertThat(confirmedList).allMatch(o -> o.getStatus() == OrderStatus.CONFIRMED);
        assertThat(confirmedList).anyMatch(o -> o.getId().equals(confirmed.getId()));
    }

    @Test
    void findByMemberId_paginated() {
        for (int i = 1; i <= 5; i++) {
            orderMapper.insertOrder(buildOrder("Address " + i, new BigDecimal(i * 10)));
        }

        List<Order> page0 = orderMapper.findByMemberId(member.getId(), 0, 2);
        List<Order> page1 = orderMapper.findByMemberId(member.getId(), 2, 2);
        List<Order> page2 = orderMapper.findByMemberId(member.getId(), 4, 2);

        assertThat(page0).hasSize(2);
        assertThat(page1).hasSize(2);
        assertThat(page2).hasSize(1);

        List<Long> ids0 = page0.stream().map(Order::getId).toList();
        List<Long> ids1 = page1.stream().map(Order::getId).toList();
        assertThat(ids0).doesNotContainAnyElementsOf(ids1);

        int total = orderMapper.countByMemberId(member.getId());
        assertThat(total).isEqualTo(5);
    }
}
