package com.example.shop.mapper;

import com.example.shop.domain.Member;

import java.util.List;
import java.util.Map;

public interface MemberMapper {

    void insert(Member member);

    Member selectById(Long id);

    Member selectByEmail(String email);

    List<Member> selectAll(Map<String, Object> params);

    void update(Member member);

    void delete(Long id);

    int count();
}
