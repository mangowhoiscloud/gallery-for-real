package com.example.shop.controller;

import com.example.shop.dto.CartItemAddRequest;
import com.example.shop.dto.CartItemUpdateRequest;
import com.example.shop.dto.CartResponse;
import com.example.shop.service.CartService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/cart")
public class CartController {

    private final CartService cartService;

    public CartController(CartService cartService) {
        this.cartService = cartService;
    }

    // GET /api/cart — get current user's cart (auto-created if not exists)
    @GetMapping
    public ResponseEntity<CartResponse> getCart(@AuthenticationPrincipal UserDetails userDetails) {
        return ResponseEntity.ok(cartService.getCart(userDetails.getUsername()));
    }

    // POST /api/cart/items — add item (increments qty if product already in cart)
    @PostMapping("/items")
    public ResponseEntity<CartResponse> addItem(
            @AuthenticationPrincipal UserDetails userDetails,
            @Valid @RequestBody CartItemAddRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(cartService.addItem(userDetails.getUsername(), request));
    }

    // PUT /api/cart/items/{itemId} — update item quantity
    @PutMapping("/items/{itemId}")
    public ResponseEntity<CartResponse> updateItem(
            @AuthenticationPrincipal UserDetails userDetails,
            @PathVariable Long itemId,
            @Valid @RequestBody CartItemUpdateRequest request) {
        return ResponseEntity.ok(cartService.updateItem(userDetails.getUsername(), itemId, request));
    }

    // DELETE /api/cart/items/{itemId} — remove single item
    @DeleteMapping("/items/{itemId}")
    public ResponseEntity<Void> removeItem(
            @AuthenticationPrincipal UserDetails userDetails,
            @PathVariable Long itemId) {
        cartService.removeItem(userDetails.getUsername(), itemId);
        return ResponseEntity.noContent().build();
    }

    // DELETE /api/cart — clear all items from cart
    @DeleteMapping
    public ResponseEntity<Void> clearCart(@AuthenticationPrincipal UserDetails userDetails) {
        cartService.clearCart(userDetails.getUsername());
        return ResponseEntity.noContent().build();
    }
}
