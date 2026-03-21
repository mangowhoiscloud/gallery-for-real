package com.example.shop.service;

import com.example.shop.dto.*;
import com.example.shop.entity.*;
import com.example.shop.mapper.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.NoSuchElementException;

@Service
@Transactional
public class OrderService {

    private final OrderMapper orderMapper;
    private final OrderItemMapper orderItemMapper;
    private final CartMapper cartMapper;
    private final CartItemMapper cartItemMapper;
    private final ProductMapper productMapper;
    private final MemberMapper memberMapper;

    public OrderService(OrderMapper orderMapper, OrderItemMapper orderItemMapper,
                        CartMapper cartMapper, CartItemMapper cartItemMapper,
                        ProductMapper productMapper, MemberMapper memberMapper) {
        this.orderMapper = orderMapper;
        this.orderItemMapper = orderItemMapper;
        this.cartMapper = cartMapper;
        this.cartItemMapper = cartItemMapper;
        this.productMapper = productMapper;
        this.memberMapper = memberMapper;
    }

    public OrderResponse createOrder(String email, OrderCreateRequest request) {
        Member member = requireMember(email);
        Cart cart = cartMapper.findByMemberId(member.getId());
        if (cart == null) {
            throw new IllegalArgumentException("Cart is empty");
        }

        List<CartItemResponse> cartItems = cartItemMapper.findCartItems(cart.getId());
        if (cartItems.isEmpty()) {
            throw new IllegalArgumentException("Cart is empty");
        }

        // Validate all products are ACTIVE and have sufficient stock
        List<String> errors = new ArrayList<>();
        for (CartItemResponse ci : cartItems) {
            Product product = productMapper.findById(ci.productId());
            if (product == null || product.getStatus() != ProductStatus.ACTIVE) {
                errors.add("Product is not available: " + ci.productName());
            } else if (product.getStockQuantity() < ci.quantity()) {
                errors.add("Insufficient stock for " + ci.productName()
                        + ". Available: " + product.getStockQuantity()
                        + ", Requested: " + ci.quantity());
            }
        }
        if (!errors.isEmpty()) {
            throw new IllegalArgumentException(String.join("; ", errors));
        }

        // Calculate total amount from cart items (snapshot prices)
        BigDecimal totalAmount = BigDecimal.ZERO;
        for (CartItemResponse ci : cartItems) {
            totalAmount = totalAmount.add(ci.productPrice().multiply(BigDecimal.valueOf(ci.quantity())));
        }

        // Create order
        Order order = new Order();
        order.setMemberId(member.getId());
        order.setTotalAmount(totalAmount);
        order.setStatus(OrderStatus.PENDING);
        order.setShippingAddress(request.shippingAddress());
        orderMapper.insertOrder(order);

        // Create order items (snapshot product name/price) and decrease stock
        for (CartItemResponse ci : cartItems) {
            OrderItem oi = new OrderItem();
            oi.setOrderId(order.getId());
            oi.setProductId(ci.productId());
            oi.setProductName(ci.productName());
            oi.setQuantity(ci.quantity());
            oi.setUnitPrice(ci.productPrice());
            orderItemMapper.insertOrderItem(oi);

            productMapper.decreaseStock(ci.productId(), ci.quantity());
        }

        // Clear cart
        cartItemMapper.deleteAllItems(cart.getId());

        return orderMapper.findById(order.getId());
    }

    @Transactional(readOnly = true)
    public OrderPageResponse getMyOrders(String email, int page, int size) {
        Member member = requireMember(email);
        size = Math.min(size, 100);
        int offset = page * size;
        List<Order> orders = orderMapper.findByMemberId(member.getId(), offset, size);
        int total = orderMapper.countByMemberId(member.getId());
        int totalPages = (total + size - 1) / size;

        List<OrderResponse> content = orders.stream().map(o -> {
            OrderResponse resp = new OrderResponse();
            resp.setId(o.getId());
            resp.setMemberId(o.getMemberId());
            resp.setTotalAmount(o.getTotalAmount());
            resp.setStatus(o.getStatus());
            resp.setShippingAddress(o.getShippingAddress());
            resp.setCreatedAt(o.getCreatedAt());
            resp.setUpdatedAt(o.getUpdatedAt());
            resp.setItems(List.of());
            return resp;
        }).toList();

        return new OrderPageResponse(content, totalPages, total, page, size);
    }

    @Transactional(readOnly = true)
    public OrderResponse getOrderDetail(String email, Long orderId) {
        Member member = requireMember(email);
        OrderResponse order = orderMapper.findById(orderId);
        if (order == null) {
            throw new NoSuchElementException("Order not found: " + orderId);
        }
        // Non-admin can only see their own orders
        if (member.getRole() != MemberRole.ADMIN && !order.getMemberId().equals(member.getId())) {
            throw new NoSuchElementException("Order not found: " + orderId);
        }
        return order;
    }

    public OrderResponse updateStatus(Long orderId, OrderStatusUpdateRequest request) {
        OrderResponse order = orderMapper.findById(orderId);
        if (order == null) {
            throw new NoSuchElementException("Order not found: " + orderId);
        }

        validateStatusTransition(order.getStatus(), request.status());

        orderMapper.updateStatus(orderId, request.status());
        return orderMapper.findById(orderId);
    }

    public OrderResponse cancelOrder(String email, Long orderId) {
        Member member = requireMember(email);
        OrderResponse order = orderMapper.findById(orderId);
        if (order == null) {
            throw new NoSuchElementException("Order not found: " + orderId);
        }
        if (!order.getMemberId().equals(member.getId())) {
            throw new NoSuchElementException("Order not found: " + orderId);
        }
        if (order.getStatus() != OrderStatus.PENDING) {
            throw new IllegalArgumentException("Only PENDING orders can be cancelled");
        }

        // Restore stock for each item
        for (OrderItemResponse item : order.getItems()) {
            productMapper.increaseStock(item.productId(), item.quantity());
        }

        orderMapper.updateStatus(orderId, OrderStatus.CANCELLED);
        return orderMapper.findById(orderId);
    }

    @Transactional(readOnly = true)
    public OrderPageResponse getAllOrders(String status, int page, int size) {
        size = Math.min(size, 100);
        int offset = page * size;
        List<Order> orders = orderMapper.findAll(status, offset, size);
        int total = orderMapper.countAll(status);
        int totalPages = (total + size - 1) / size;

        List<OrderResponse> content = orders.stream().map(o -> {
            OrderResponse resp = new OrderResponse();
            resp.setId(o.getId());
            resp.setMemberId(o.getMemberId());
            resp.setTotalAmount(o.getTotalAmount());
            resp.setStatus(o.getStatus());
            resp.setShippingAddress(o.getShippingAddress());
            resp.setCreatedAt(o.getCreatedAt());
            resp.setUpdatedAt(o.getUpdatedAt());
            resp.setItems(List.of());
            return resp;
        }).toList();

        return new OrderPageResponse(content, totalPages, total, page, size);
    }

    private void validateStatusTransition(OrderStatus current, OrderStatus next) {
        boolean valid = switch (current) {
            case PENDING -> next == OrderStatus.CONFIRMED;
            case CONFIRMED -> next == OrderStatus.SHIPPED;
            case SHIPPED -> next == OrderStatus.DELIVERED;
            case DELIVERED, CANCELLED -> false;
        };
        if (!valid) {
            throw new IllegalArgumentException(
                    "Invalid status transition: " + current + " -> " + next);
        }
    }

    private Member requireMember(String email) {
        Member member = memberMapper.findByEmail(email);
        if (member == null) {
            throw new NoSuchElementException("Member not found: " + email);
        }
        return member;
    }
}
