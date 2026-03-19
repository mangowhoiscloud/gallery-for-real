package com.example.shop.mapper;

import com.example.shop.config.TestConfig;
import com.example.shop.domain.Member;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.*;

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes = TestConfig.class)
@Transactional
public class MemberMapperTest {

    @Autowired
    private MemberMapper memberMapper;

    private Member buildMember(String email) {
        Member m = new Member();
        m.setEmail(email);
        m.setPassword("hashed_password");
        m.setName("Test User");
        m.setPhone("010-1234-5678");
        m.setAddress("Seoul, Korea");
        m.setRole(Member.Role.USER);
        return m;
    }

    @Test
    public void insertAndSelectById() {
        Member m = buildMember("user1@example.com");
        memberMapper.insert(m);

        assertNotNull("Generated key must be set", m.getId());

        Member found = memberMapper.selectById(m.getId());
        assertNotNull(found);
        assertEquals("user1@example.com", found.getEmail());
        assertEquals("Test User", found.getName());
        assertEquals(Member.Role.USER, found.getRole());
        assertNotNull(found.getCreatedAt());
    }

    @Test
    public void selectByEmail() {
        Member m = buildMember("byemail@example.com");
        memberMapper.insert(m);

        Member found = memberMapper.selectByEmail("byemail@example.com");
        assertNotNull(found);
        assertEquals(m.getId(), found.getId());
        assertEquals("byemail@example.com", found.getEmail());
    }

    @Test
    public void selectByEmailReturnsNullWhenNotFound() {
        Member found = memberMapper.selectByEmail("nobody@example.com");
        assertNull(found);
    }

    @Test
    public void updateFields() {
        Member m = buildMember("update@example.com");
        memberMapper.insert(m);

        m.setName("Updated Name");
        m.setPhone("010-9999-8888");
        m.setAddress("Busan, Korea");
        m.setPassword("new_hashed_password");
        memberMapper.update(m);

        Member updated = memberMapper.selectById(m.getId());
        assertEquals("Updated Name", updated.getName());
        assertEquals("010-9999-8888", updated.getPhone());
        assertEquals("Busan, Korea", updated.getAddress());
        assertEquals("new_hashed_password", updated.getPassword());
    }

    @Test
    public void delete() {
        Member m = buildMember("delete@example.com");
        memberMapper.insert(m);
        Long id = m.getId();

        memberMapper.delete(id);

        Member found = memberMapper.selectById(id);
        assertNull(found);
    }

    @Test
    public void selectAllWithPagination() {
        for (int i = 1; i <= 5; i++) {
            memberMapper.insert(buildMember("page" + i + "@example.com"));
        }

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("offset", 0);
        params.put("limit", 3);
        List<Member> page1 = memberMapper.selectAll(params);
        assertEquals(3, page1.size());

        params.put("offset", 3);
        params.put("limit", 3);
        List<Member> page2 = memberMapper.selectAll(params);
        assertEquals(2, page2.size());
    }

    @Test
    public void countReturnsCorrectTotal() {
        int before = memberMapper.count();

        memberMapper.insert(buildMember("count1@example.com"));
        memberMapper.insert(buildMember("count2@example.com"));

        assertEquals(before + 2, memberMapper.count());
    }

    @Test(expected = DataIntegrityViolationException.class)
    public void duplicateEmailInsertFails() {
        memberMapper.insert(buildMember("dup@example.com"));
        memberMapper.insert(buildMember("dup@example.com"));
    }

    @Test
    public void adminRolePersists() {
        Member admin = buildMember("admin@example.com");
        admin.setRole(Member.Role.ADMIN);
        memberMapper.insert(admin);

        Member found = memberMapper.selectById(admin.getId());
        assertEquals(Member.Role.ADMIN, found.getRole());
    }
}
