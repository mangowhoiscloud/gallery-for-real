package com.example.shop.controller;

import com.example.shop.dto.OrderCreateRequest;
import com.example.shop.dto.OrderResponse;
import com.example.shop.dto.OrderStatusUpdateRequest;
import com.example.shop.dto.PageResponse;
import com.example.shop.service.OrderService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;

@RestController
public class OrderController {

    @Autowired
    private OrderService orderService;

    @PostMapping("/api/orders")
    public ResponseEntity<OrderResponse> createOrder(Authentication auth,
                                                     @RequestBody OrderCreateRequest request) {
        OrderResponse response = orderService.createOrder(auth.getName(), request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/api/orders")
    public ResponseEntity<PageResponse<OrderResponse>> getMyOrders(
            Authentication auth,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(orderService.getMyOrders(auth.getName(), page, size));
    }

    @GetMapping("/api/orders/{id}")
    public ResponseEntity<OrderResponse> getOrderDetail(Authentication auth,
                                                        @PathVariable Long id) {
        boolean isAdmin = auth.getAuthorities().stream()
                .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN"));
        return ResponseEntity.ok(orderService.getOrderDetail(auth.getName(), id, isAdmin));
    }

    @PutMapping("/api/orders/{id}/cancel")
    public ResponseEntity<Void> cancelOrder(Authentication auth, @PathVariable Long id) {
        orderService.cancelOrder(auth.getName(), id);
        return ResponseEntity.noContent().build();
    }

    @PutMapping("/api/admin/orders/{id}/status")
    public ResponseEntity<OrderResponse> updateStatus(@PathVariable Long id,
                                                      @Valid @RequestBody OrderStatusUpdateRequest request) {
        return ResponseEntity.ok(orderService.updateStatus(id, request.getStatus()));
    }

    @GetMapping("/api/admin/orders")
    public ResponseEntity<PageResponse<OrderResponse>> getAllOrders(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(orderService.getAllOrders(page, size));
    }
}
