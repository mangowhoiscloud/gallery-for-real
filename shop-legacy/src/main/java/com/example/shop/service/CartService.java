package com.example.shop.service;

import com.example.shop.domain.Cart;
import com.example.shop.domain.CartItem;
import com.example.shop.domain.Member;
import com.example.shop.domain.Product;
import com.example.shop.dto.CartAddItemRequest;
import com.example.shop.dto.CartItemResponse;
import com.example.shop.dto.CartResponse;
import com.example.shop.dto.CartUpdateItemRequest;
import com.example.shop.exception.BusinessException;
import com.example.shop.mapper.CartItemMapper;
import com.example.shop.mapper.CartMapper;
import com.example.shop.mapper.MemberMapper;
import com.example.shop.mapper.ProductMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Transactional
public class CartService {

    @Autowired private CartMapper cartMapper;
    @Autowired private CartItemMapper cartItemMapper;
    @Autowired private MemberMapper memberMapper;
    @Autowired private ProductMapper productMapper;

    public CartResponse getCart(String email) {
        Member member = getMember(email);
        Cart cart = getOrCreateCart(member.getId());
        List<CartItem> items = cartItemMapper.selectByCartId(cart.getId());
        return toResponse(items);
    }

    public CartResponse addItem(String email, CartAddItemRequest request) {
        Member member = getMember(email);
        Cart cart = getOrCreateCart(member.getId());

        Product product = productMapper.selectById(request.getProductId());
        if (product == null || product.getStatus() != Product.Status.ACTIVE) {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "Product is not available");
        }

        List<CartItem> existingItems = cartItemMapper.selectByCartId(cart.getId());
        CartItem existing = null;
        for (CartItem item : existingItems) {
            if (request.getProductId().equals(item.getProductId())) {
                existing = item;
                break;
            }
        }

        int newQuantity = request.getQuantity();
        if (existing != null) {
            newQuantity = existing.getQuantity() + request.getQuantity();
        }

        if (newQuantity > product.getStockQuantity()) {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "Insufficient stock");
        }

        if (existing != null) {
            Map<String, Object> params = new HashMap<String, Object>();
            params.put("id", existing.getId());
            params.put("quantity", newQuantity);
            cartItemMapper.updateQuantity(params);
        } else {
            CartItem cartItem = new CartItem();
            cartItem.setCartId(cart.getId());
            cartItem.setProductId(request.getProductId());
            cartItem.setQuantity(newQuantity);
            cartItemMapper.insert(cartItem);
        }

        List<CartItem> items = cartItemMapper.selectByCartId(cart.getId());
        return toResponse(items);
    }

    public CartResponse updateItemQuantity(String email, Long itemId, CartUpdateItemRequest request) {
        Member member = getMember(email);
        Cart cart = getOrCreateCart(member.getId());

        CartItem cartItem = cartItemMapper.selectById(itemId);
        if (cartItem == null || !cartItem.getCartId().equals(cart.getId())) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Cart item not found");
        }

        Product product = productMapper.selectById(cartItem.getProductId());
        if (product == null || product.getStatus() != Product.Status.ACTIVE) {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "Product is not available");
        }
        if (request.getQuantity() > product.getStockQuantity()) {
            throw new BusinessException(HttpStatus.BAD_REQUEST, "Insufficient stock");
        }

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("id", itemId);
        params.put("quantity", request.getQuantity());
        cartItemMapper.updateQuantity(params);

        List<CartItem> items = cartItemMapper.selectByCartId(cart.getId());
        return toResponse(items);
    }

    public void removeItem(String email, Long itemId) {
        Member member = getMember(email);
        Cart cart = cartMapper.selectByMemberId(member.getId());
        if (cart == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Cart item not found");
        }

        CartItem cartItem = cartItemMapper.selectById(itemId);
        if (cartItem == null || !cartItem.getCartId().equals(cart.getId())) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Cart item not found");
        }

        cartItemMapper.deleteById(itemId);
    }

    public void clearCart(String email) {
        Member member = getMember(email);
        Cart cart = getOrCreateCart(member.getId());
        cartItemMapper.deleteByCartId(cart.getId());
    }

    private Member getMember(String email) {
        Member member = memberMapper.selectByEmail(email);
        if (member == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Member not found");
        }
        return member;
    }

    private Cart getOrCreateCart(Long memberId) {
        Cart cart = cartMapper.selectByMemberId(memberId);
        if (cart == null) {
            cart = new Cart();
            cart.setMemberId(memberId);
            cartMapper.insert(cart);
        }
        return cart;
    }

    private CartResponse toResponse(List<CartItem> items) {
        CartResponse response = new CartResponse();
        List<CartItemResponse> itemResponses = new ArrayList<CartItemResponse>();
        BigDecimal cartTotal = BigDecimal.ZERO;

        for (CartItem item : items) {
            CartItemResponse itemResponse = new CartItemResponse();
            itemResponse.setId(item.getId());
            itemResponse.setProductId(item.getProductId());
            itemResponse.setProductName(item.getProductName());
            itemResponse.setUnitPrice(item.getUnitPrice());
            itemResponse.setQuantity(item.getQuantity());
            if (item.getUnitPrice() != null) {
                BigDecimal subtotal = item.getUnitPrice().multiply(new BigDecimal(item.getQuantity()));
                itemResponse.setSubtotal(subtotal);
                cartTotal = cartTotal.add(subtotal);
            }
            itemResponse.setProductStatus(item.getProductStatus());
            itemResponses.add(itemResponse);
        }

        response.setItems(itemResponses);
        response.setCartTotal(cartTotal);
        return response;
    }
}
