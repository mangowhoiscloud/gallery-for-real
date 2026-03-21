package com.example.shop.controller;

import com.example.shop.dto.OrderCreateRequest;
import com.example.shop.dto.OrderPageResponse;
import com.example.shop.dto.OrderResponse;
import com.example.shop.dto.OrderStatusUpdateRequest;
import com.example.shop.service.OrderService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

@RestController
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    // POST /api/orders — Create order from cart
    @PostMapping("/api/orders")
    public ResponseEntity<OrderResponse> createOrder(
            @AuthenticationPrincipal UserDetails userDetails,
            @Valid @RequestBody OrderCreateRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(orderService.createOrder(userDetails.getUsername(), request));
    }

    // GET /api/orders — List my orders (paginated)
    @GetMapping("/api/orders")
    public ResponseEntity<OrderPageResponse> getMyOrders(
            @AuthenticationPrincipal UserDetails userDetails,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(orderService.getMyOrders(userDetails.getUsername(), page, size));
    }

    // GET /api/orders/{id} — Get order detail (owner or admin)
    @GetMapping("/api/orders/{id}")
    public ResponseEntity<OrderResponse> getOrderDetail(
            @AuthenticationPrincipal UserDetails userDetails,
            @PathVariable Long id) {
        return ResponseEntity.ok(orderService.getOrderDetail(userDetails.getUsername(), id));
    }

    // PUT /api/orders/{id}/status — Admin update status
    @PutMapping("/api/orders/{id}/status")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<OrderResponse> updateStatus(
            @PathVariable Long id,
            @Valid @RequestBody OrderStatusUpdateRequest request) {
        return ResponseEntity.ok(orderService.updateStatus(id, request));
    }

    // PUT /api/orders/{id}/cancel — User cancel own order
    @PutMapping("/api/orders/{id}/cancel")
    public ResponseEntity<OrderResponse> cancelOrder(
            @AuthenticationPrincipal UserDetails userDetails,
            @PathVariable Long id) {
        return ResponseEntity.ok(orderService.cancelOrder(userDetails.getUsername(), id));
    }

    // GET /api/admin/orders — Admin list all orders (paginated, optional status filter)
    @GetMapping("/api/admin/orders")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<OrderPageResponse> getAllOrders(
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(orderService.getAllOrders(status, page, size));
    }
}
