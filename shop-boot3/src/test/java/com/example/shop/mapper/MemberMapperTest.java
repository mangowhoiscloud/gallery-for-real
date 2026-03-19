package com.example.shop.mapper;

import com.example.shop.entity.Member;
import com.example.shop.entity.MemberRole;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
@Transactional
class MemberMapperTest {

    @Autowired
    MemberMapper memberMapper;

    @Autowired
    PasswordEncoder passwordEncoder;

    private Member buildMember(String email) {
        Member m = new Member();
        m.setEmail(email);
        m.setPassword(passwordEncoder.encode("password123"));
        m.setName("Test User");
        m.setPhone("01012345678");
        m.setAddress("Seoul");
        m.setRole(MemberRole.USER);
        m.setActive(true);
        return m;
    }

    @Test
    void insertAndFindByEmail() {
        Member m = buildMember("insert@example.com");
        memberMapper.insert(m);

        assertThat(m.getId()).isNotNull();

        Member found = memberMapper.findByEmail("insert@example.com");
        assertThat(found).isNotNull();
        assertThat(found.getEmail()).isEqualTo("insert@example.com");
        assertThat(found.getName()).isEqualTo("Test User");
        assertThat(found.getRole()).isEqualTo(MemberRole.USER);
        assertThat(found.getActive()).isTrue();
    }

    @Test
    void findById_returnsCorrectFields() {
        Member m = buildMember("findbyid@example.com");
        memberMapper.insert(m);

        Member found = memberMapper.findById(m.getId());
        assertThat(found).isNotNull();
        assertThat(found.getId()).isEqualTo(m.getId());
        assertThat(found.getEmail()).isEqualTo("findbyid@example.com");
        assertThat(found.getPhone()).isEqualTo("01012345678");
        assertThat(found.getAddress()).isEqualTo("Seoul");
        assertThat(found.getCreatedAt()).isNotNull();
        assertThat(found.getUpdatedAt()).isNotNull();
    }

    @Test
    void update_modifiesNamePhoneAddress() {
        Member m = buildMember("update@example.com");
        memberMapper.insert(m);

        m.setName("Updated Name");
        m.setPhone("01099999999");
        m.setAddress("Busan");
        memberMapper.update(m);

        Member found = memberMapper.findById(m.getId());
        assertThat(found.getName()).isEqualTo("Updated Name");
        assertThat(found.getPhone()).isEqualTo("01099999999");
        assertThat(found.getAddress()).isEqualTo("Busan");
    }

    @Test
    void deactivate_setsActiveFalse() {
        Member m = buildMember("deactivate@example.com");
        memberMapper.insert(m);

        memberMapper.deactivate(m.getId());

        Member found = memberMapper.findById(m.getId());
        assertThat(found.getActive()).isFalse();
    }

    @Test
    void findAll_returnsPaginatedResults() {
        memberMapper.insert(buildMember("page1@example.com"));
        memberMapper.insert(buildMember("page2@example.com"));
        memberMapper.insert(buildMember("page3@example.com"));

        List<Member> firstPage = memberMapper.findAll(0, 2);
        assertThat(firstPage).hasSize(2);

        int total = memberMapper.countAll();
        assertThat(total).isGreaterThanOrEqualTo(3);
    }
}
