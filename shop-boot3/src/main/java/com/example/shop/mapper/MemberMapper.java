package com.example.shop.mapper;

import com.example.shop.entity.Member;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface MemberMapper {

    void insert(Member member);

    Member findByEmail(String email);

    Member findById(Long id);

    List<Member> findAll(@Param("offset") int offset, @Param("limit") int limit);

    int countAll();

    void update(Member member);

    void deactivate(Long id);
}
