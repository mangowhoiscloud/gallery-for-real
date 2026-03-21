package com.example.shop.controller;

import com.example.shop.dto.MemberLoginRequest;
import com.example.shop.dto.MemberRegisterRequest;
import com.example.shop.dto.MemberResponse;
import com.example.shop.dto.MemberUpdateRequest;
import com.example.shop.dto.PageResponse;
import com.example.shop.service.MemberService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;

@RestController
@RequestMapping("/api/members")
public class MemberController {

    @Autowired
    private MemberService memberService;

    @PostMapping
    public ResponseEntity<MemberResponse> register(@Valid @RequestBody MemberRegisterRequest request) {
        MemberResponse response = memberService.register(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @PostMapping("/login")
    public ResponseEntity<MemberResponse> login(@Valid @RequestBody MemberLoginRequest request) {
        MemberResponse response = memberService.login(request);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/me")
    public ResponseEntity<MemberResponse> getProfile(Authentication auth) {
        return ResponseEntity.ok(memberService.getProfile(auth.getName()));
    }

    @PutMapping("/me")
    public ResponseEntity<MemberResponse> updateProfile(Authentication auth,
                                                        @Valid @RequestBody MemberUpdateRequest request) {
        return ResponseEntity.ok(memberService.updateProfile(auth.getName(), request));
    }

    @DeleteMapping("/me")
    public ResponseEntity<Void> deleteMember(Authentication auth) {
        memberService.deleteMember(auth.getName());
        return ResponseEntity.noContent().build();
    }

    @GetMapping
    public ResponseEntity<PageResponse<MemberResponse>> listAll(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(memberService.listAll(page, size));
    }

    @GetMapping("/{id}")
    public ResponseEntity<MemberResponse> getById(@PathVariable Long id) {
        return ResponseEntity.ok(memberService.getById(id));
    }
}
