package com.example.shop.service;

import com.example.shop.domain.Cart;
import com.example.shop.domain.CartItem;
import com.example.shop.domain.Member;
import com.example.shop.domain.Order;
import com.example.shop.domain.OrderItem;
import com.example.shop.domain.Product;
import com.example.shop.dto.OrderCreateRequest;
import com.example.shop.dto.OrderItemResponse;
import com.example.shop.dto.OrderResponse;
import com.example.shop.dto.PageResponse;
import com.example.shop.exception.BusinessException;
import com.example.shop.mapper.CartItemMapper;
import com.example.shop.mapper.CartMapper;
import com.example.shop.mapper.MemberMapper;
import com.example.shop.mapper.OrderItemMapper;
import com.example.shop.mapper.OrderMapper;
import com.example.shop.mapper.ProductMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Transactional
public class OrderService {

    @Autowired private OrderMapper orderMapper;
    @Autowired private OrderItemMapper orderItemMapper;
    @Autowired private CartMapper cartMapper;
    @Autowired private CartItemMapper cartItemMapper;
    @Autowired private ProductMapper productMapper;
    @Autowired private MemberMapper memberMapper;

    private static final Map<Order.Status, Order.Status> VALID_TRANSITIONS = new HashMap<Order.Status, Order.Status>();
    static {
        VALID_TRANSITIONS.put(Order.Status.PENDING, Order.Status.CONFIRMED);
        VALID_TRANSITIONS.put(Order.Status.CONFIRMED, Order.Status.SHIPPED);
        VALID_TRANSITIONS.put(Order.Status.SHIPPED, Order.Status.DELIVERED);
    }

    public OrderResponse createOrder(String email, OrderCreateRequest request) {
        Member member = getMember(email);

        // Resolve shipping address: request body > member profile
        String shippingAddress = request.getShippingAddress();
        if (shippingAddress == null || shippingAddress.trim().isEmpty()) {
            shippingAddress = member.getAddress();
        }
        if (shippingAddress == null || shippingAddress.trim().isEmpty()) {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "Shipping address is required");
        }

        // Get cart items
        Cart cart = cartMapper.selectByMemberId(member.getId());
        if (cart == null) {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "Cart is empty");
        }
        List<CartItem> cartItems = cartItemMapper.selectByCartId(cart.getId());
        if (cartItems.isEmpty()) {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "Cart is empty");
        }

        // Validate all products and build order items
        BigDecimal totalAmount = BigDecimal.ZERO;
        List<OrderItem> orderItems = new ArrayList<OrderItem>();

        for (CartItem cartItem : cartItems) {
            Product product = productMapper.selectById(cartItem.getProductId());
            if (product == null || product.getStatus() != Product.Status.ACTIVE) {
                throw new BusinessException(HttpStatus.BAD_REQUEST,
                        "Product is not available: " + (product != null ? product.getName() : "unknown"));
            }
            if (cartItem.getQuantity() > product.getStockQuantity()) {
                throw new BusinessException(HttpStatus.BAD_REQUEST,
                        "Insufficient stock for product: " + product.getName());
            }

            OrderItem orderItem = new OrderItem();
            orderItem.setProductId(product.getId());
            orderItem.setProductName(product.getName());
            orderItem.setQuantity(cartItem.getQuantity());
            orderItem.setUnitPrice(product.getPrice());
            orderItems.add(orderItem);

            totalAmount = totalAmount.add(product.getPrice().multiply(new BigDecimal(cartItem.getQuantity())));
        }

        // Create order
        Order order = new Order();
        order.setMemberId(member.getId());
        order.setTotalAmount(totalAmount);
        order.setStatus(Order.Status.PENDING);
        order.setShippingAddress(shippingAddress);
        orderMapper.insert(order);

        // Set orderId on all items and batch insert
        for (OrderItem item : orderItems) {
            item.setOrderId(order.getId());
        }
        orderItemMapper.insertBatch(orderItems);

        // Decrease product stock
        for (OrderItem item : orderItems) {
            Map<String, Object> stockParams = new HashMap<String, Object>();
            stockParams.put("id", item.getProductId());
            stockParams.put("delta", -item.getQuantity());
            productMapper.updateStock(stockParams);
        }

        // Clear cart
        cartItemMapper.deleteByCartId(cart.getId());

        // Build response
        return toOrderResponse(order, orderItems);
    }

    public PageResponse<OrderResponse> getMyOrders(String email, int page, int size) {
        Member member = getMember(email);
        Map<String, Object> params = new HashMap<String, Object>();
        params.put("memberId", member.getId());
        params.put("limit", size);
        params.put("offset", page * size);
        List<Order> orders = orderMapper.selectByMemberId(params);
        int total = orderMapper.countByMemberId(member.getId());
        List<OrderResponse> content = new ArrayList<OrderResponse>();
        for (Order order : orders) {
            List<OrderItem> items = orderItemMapper.selectByOrderId(order.getId());
            content.add(toOrderResponse(order, items));
        }
        return new PageResponse<OrderResponse>(content, total, page, size);
    }

    public OrderResponse getOrderDetail(String email, Long orderId, boolean isAdmin) {
        Order order = orderMapper.selectById(orderId);
        if (order == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Order not found");
        }
        if (!isAdmin) {
            Member member = getMember(email);
            if (!order.getMemberId().equals(member.getId())) {
                throw new BusinessException(HttpStatus.FORBIDDEN, "Access denied");
            }
        }
        List<OrderItem> items = orderItemMapper.selectByOrderId(orderId);
        return toOrderResponse(order, items);
    }

    public OrderResponse updateStatus(Long orderId, String statusStr) {
        Order order = orderMapper.selectById(orderId);
        if (order == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Order not found");
        }

        Order.Status newStatus;
        try {
            newStatus = Order.Status.valueOf(statusStr);
        } catch (IllegalArgumentException e) {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "Invalid status: " + statusStr);
        }

        Order.Status expectedNext = VALID_TRANSITIONS.get(order.getStatus());
        if (expectedNext == null || !expectedNext.equals(newStatus)) {
            throw new BusinessException(HttpStatus.BAD_REQUEST,
                    "Invalid status transition from " + order.getStatus() + " to " + newStatus);
        }

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("id", orderId);
        params.put("status", newStatus);
        orderMapper.updateStatus(params);

        order.setStatus(newStatus);
        List<OrderItem> items = orderItemMapper.selectByOrderId(orderId);
        return toOrderResponse(order, items);
    }

    public void cancelOrder(String email, Long orderId) {
        Member member = getMember(email);
        Order order = orderMapper.selectById(orderId);
        if (order == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Order not found");
        }
        if (!order.getMemberId().equals(member.getId())) {
            throw new BusinessException(HttpStatus.FORBIDDEN, "Access denied");
        }
        if (order.getStatus() != Order.Status.PENDING) {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "Only PENDING orders can be cancelled");
        }

        // Restore stock
        List<OrderItem> items = orderItemMapper.selectByOrderId(orderId);
        for (OrderItem item : items) {
            if (item.getProductId() != null) {
                Map<String, Object> stockParams = new HashMap<String, Object>();
                stockParams.put("id", item.getProductId());
                stockParams.put("delta", item.getQuantity());
                productMapper.updateStock(stockParams);
            }
        }

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("id", orderId);
        params.put("status", Order.Status.CANCELLED);
        orderMapper.updateStatus(params);
    }

    public PageResponse<OrderResponse> getAllOrders(int page, int size) {
        Map<String, Object> params = new HashMap<String, Object>();
        params.put("limit", size);
        params.put("offset", page * size);
        List<Order> orders = orderMapper.selectAll(params);
        int total = orderMapper.countAll();
        List<OrderResponse> content = new ArrayList<OrderResponse>();
        for (Order order : orders) {
            List<OrderItem> items = orderItemMapper.selectByOrderId(order.getId());
            content.add(toOrderResponse(order, items));
        }
        return new PageResponse<OrderResponse>(content, total, page, size);
    }

    private Member getMember(String email) {
        Member member = memberMapper.selectByEmail(email);
        if (member == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Member not found");
        }
        return member;
    }

    private OrderResponse toOrderResponse(Order order, List<OrderItem> items) {
        OrderResponse response = new OrderResponse();
        response.setId(order.getId());
        response.setTotalAmount(order.getTotalAmount());
        response.setStatus(order.getStatus().name());
        response.setShippingAddress(order.getShippingAddress());
        response.setCreatedAt(order.getCreatedAt());

        List<OrderItemResponse> itemResponses = new ArrayList<OrderItemResponse>();
        for (OrderItem item : items) {
            OrderItemResponse itemResponse = new OrderItemResponse();
            itemResponse.setId(item.getId());
            itemResponse.setProductId(item.getProductId());
            itemResponse.setProductName(item.getProductName());
            itemResponse.setQuantity(item.getQuantity());
            itemResponse.setUnitPrice(item.getUnitPrice());
            itemResponse.setSubtotal(item.getUnitPrice().multiply(new BigDecimal(item.getQuantity())));
            itemResponses.add(itemResponse);
        }
        response.setItems(itemResponses);
        return response;
    }
}
