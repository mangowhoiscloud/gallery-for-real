package com.example.shop.service;

import com.example.shop.domain.Member;
import com.example.shop.domain.Order;
import com.example.shop.domain.OrderItem;
import com.example.shop.dto.MemberLoginRequest;
import com.example.shop.dto.MemberRegisterRequest;
import com.example.shop.dto.MemberResponse;
import com.example.shop.dto.MemberUpdateRequest;
import com.example.shop.dto.PageResponse;
import com.example.shop.exception.BusinessException;
import com.example.shop.mapper.MemberMapper;
import com.example.shop.mapper.OrderItemMapper;
import com.example.shop.mapper.OrderMapper;
import com.example.shop.mapper.ProductMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Transactional
public class MemberService {

    @Autowired private MemberMapper memberMapper;
    @Autowired private OrderMapper orderMapper;
    @Autowired private OrderItemMapper orderItemMapper;
    @Autowired private ProductMapper productMapper;
    @Autowired private PasswordEncoder passwordEncoder;

    public MemberResponse register(MemberRegisterRequest request) {
        if (memberMapper.selectByEmail(request.getEmail()) != null) {
            throw new BusinessException(HttpStatus.CONFLICT, "Email already exists");
        }
        Member member = new Member();
        member.setEmail(request.getEmail());
        member.setPassword(passwordEncoder.encode(request.getPassword()));
        member.setName(request.getName());
        member.setPhone(request.getPhone());
        member.setAddress(request.getAddress());
        member.setRole(Member.Role.USER);
        memberMapper.insert(member);
        return toResponse(member);
    }

    public MemberResponse login(MemberLoginRequest request) {
        Member member = memberMapper.selectByEmail(request.getEmail());
        if (member == null || !passwordEncoder.matches(request.getPassword(), member.getPassword())) {
            throw new BusinessException(HttpStatus.UNAUTHORIZED, "Invalid email or password");
        }
        return toResponse(member);
    }

    public MemberResponse getProfile(String email) {
        Member member = memberMapper.selectByEmail(email);
        if (member == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Member not found");
        }
        return toResponse(member);
    }

    public MemberResponse updateProfile(String email, MemberUpdateRequest request) {
        Member member = memberMapper.selectByEmail(email);
        if (member == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Member not found");
        }
        if (request.getName() != null) member.setName(request.getName());
        if (request.getPhone() != null) member.setPhone(request.getPhone());
        if (request.getAddress() != null) member.setAddress(request.getAddress());
        if (request.getPassword() != null) {
            member.setPassword(passwordEncoder.encode(request.getPassword()));
        }
        memberMapper.update(member);
        return toResponse(member);
    }

    public void deleteMember(String email) {
        Member member = memberMapper.selectByEmail(email);
        if (member == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Member not found");
        }
        if (orderMapper.countActiveByMemberId(member.getId()) > 0) {
            throw new BusinessException(HttpStatus.CONFLICT, "Cannot delete account with active orders");
        }
        // Cancel PENDING orders and restore stock
        List<Order> pendingOrders = orderMapper.selectPendingByMemberId(member.getId());
        for (Order order : pendingOrders) {
            List<OrderItem> items = orderItemMapper.selectByOrderId(order.getId());
            for (OrderItem item : items) {
                if (item.getProductId() != null) {
                    Map<String, Object> stockParams = new HashMap<String, Object>();
                    stockParams.put("id", item.getProductId());
                    stockParams.put("delta", item.getQuantity());
                    productMapper.updateStock(stockParams);
                }
            }
            Map<String, Object> statusParams = new HashMap<String, Object>();
            statusParams.put("id", order.getId());
            statusParams.put("status", Order.Status.CANCELLED);
            orderMapper.updateStatus(statusParams);
        }
        // Delete all orders for this member (order_items cascade via FK)
        orderMapper.deleteByMemberId(member.getId());
        // Delete member (carts and cart_items cascade via ON DELETE CASCADE)
        memberMapper.delete(member.getId());
    }

    public PageResponse<MemberResponse> listAll(int page, int size) {
        Map<String, Object> params = new HashMap<String, Object>();
        params.put("limit", size);
        params.put("offset", page * size);
        List<Member> members = memberMapper.selectAll(params);
        int total = memberMapper.count();
        List<MemberResponse> content = new ArrayList<MemberResponse>();
        for (Member m : members) {
            content.add(toResponse(m));
        }
        return new PageResponse<MemberResponse>(content, total, page, size);
    }

    public MemberResponse getById(Long id) {
        Member member = memberMapper.selectById(id);
        if (member == null) {
            throw new BusinessException(HttpStatus.NOT_FOUND, "Member not found");
        }
        return toResponse(member);
    }

    private MemberResponse toResponse(Member member) {
        MemberResponse response = new MemberResponse();
        response.setId(member.getId());
        response.setEmail(member.getEmail());
        response.setName(member.getName());
        response.setPhone(member.getPhone());
        response.setAddress(member.getAddress());
        response.setRole(member.getRole().name());
        return response;
    }
}
