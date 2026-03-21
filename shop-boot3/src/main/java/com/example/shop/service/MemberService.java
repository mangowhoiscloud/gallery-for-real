package com.example.shop.service;

import com.example.shop.dto.MemberPageResponse;
import com.example.shop.dto.MemberRegisterRequest;
import com.example.shop.dto.MemberResponse;
import com.example.shop.dto.MemberUpdateRequest;
import com.example.shop.entity.Member;
import com.example.shop.entity.MemberRole;
import com.example.shop.mapper.MemberMapper;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.NoSuchElementException;

@Service
@Transactional(readOnly = true)
public class MemberService {

    private final MemberMapper memberMapper;
    private final PasswordEncoder passwordEncoder;

    public MemberService(MemberMapper memberMapper, PasswordEncoder passwordEncoder) {
        this.memberMapper = memberMapper;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    public MemberResponse register(MemberRegisterRequest request) {
        if (memberMapper.findByEmail(request.email()) != null) {
            throw new IllegalStateException("Email already in use: " + request.email());
        }
        Member member = new Member();
        member.setEmail(request.email());
        member.setPassword(passwordEncoder.encode(request.password()));
        member.setName(request.name());
        member.setPhone(request.phone());
        member.setAddress(request.address());
        member.setRole(MemberRole.USER);
        member.setActive(true);
        memberMapper.insert(member);
        return MemberResponse.from(member);
    }

    public MemberResponse getProfile(String email) {
        Member member = memberMapper.findByEmail(email);
        if (member == null) {
            throw new NoSuchElementException("Member not found: " + email);
        }
        return MemberResponse.from(member);
    }

    @Transactional
    public MemberResponse updateProfile(String email, MemberUpdateRequest request) {
        Member member = memberMapper.findByEmail(email);
        if (member == null) {
            throw new NoSuchElementException("Member not found: " + email);
        }
        if (request.name() != null) member.setName(request.name());
        if (request.phone() != null) member.setPhone(request.phone());
        if (request.address() != null) member.setAddress(request.address());
        memberMapper.update(member);
        return MemberResponse.from(memberMapper.findById(member.getId()));
    }

    @Transactional
    public void deactivate(String email) {
        Member member = memberMapper.findByEmail(email);
        if (member == null) {
            throw new NoSuchElementException("Member not found: " + email);
        }
        memberMapper.deactivate(member.getId());
    }

    public MemberPageResponse listMembers(int page, int size) {
        if (size > 100) size = 100;
        int offset = page * size;
        List<MemberResponse> content = memberMapper.findAll(offset, size)
                .stream()
                .map(MemberResponse::from)
                .toList();
        int totalElements = memberMapper.countAll();
        int totalPages = (int) Math.ceil((double) totalElements / size);
        return new MemberPageResponse(content, totalPages, totalElements, page, size);
    }

    public MemberResponse getMemberById(Long id) {
        Member member = memberMapper.findById(id);
        if (member == null) {
            throw new NoSuchElementException("Member not found: " + id);
        }
        return MemberResponse.from(member);
    }
}
