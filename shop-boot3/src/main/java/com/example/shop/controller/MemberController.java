package com.example.shop.controller;

import com.example.shop.dto.MemberPageResponse;
import com.example.shop.dto.MemberRegisterRequest;
import com.example.shop.dto.MemberResponse;
import com.example.shop.dto.MemberUpdateRequest;
import com.example.shop.service.MemberService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/members")
public class MemberController {

    private final MemberService memberService;

    public MemberController(MemberService memberService) {
        this.memberService = memberService;
    }

    // POST /api/members — public registration
    @PostMapping
    public ResponseEntity<MemberResponse> register(@Valid @RequestBody MemberRegisterRequest request) {
        MemberResponse response = memberService.register(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    // POST /api/members/login — requires Basic Auth; returns authenticated member's profile
    @PostMapping("/login")
    public ResponseEntity<MemberResponse> login(@AuthenticationPrincipal UserDetails userDetails) {
        MemberResponse response = memberService.getProfile(userDetails.getUsername());
        return ResponseEntity.ok(response);
    }

    // GET /api/members/me — get current user profile
    @GetMapping("/me")
    public ResponseEntity<MemberResponse> getProfile(@AuthenticationPrincipal UserDetails userDetails) {
        MemberResponse response = memberService.getProfile(userDetails.getUsername());
        return ResponseEntity.ok(response);
    }

    // PUT /api/members/me — update current user profile
    @PutMapping("/me")
    public ResponseEntity<MemberResponse> updateProfile(
            @AuthenticationPrincipal UserDetails userDetails,
            @Valid @RequestBody MemberUpdateRequest request) {
        MemberResponse response = memberService.updateProfile(userDetails.getUsername(), request);
        return ResponseEntity.ok(response);
    }

    // DELETE /api/members/me — deactivate current user account
    @DeleteMapping("/me")
    public ResponseEntity<Void> deactivate(@AuthenticationPrincipal UserDetails userDetails) {
        memberService.deactivate(userDetails.getUsername());
        return ResponseEntity.noContent().build();
    }

    // GET /api/members — admin: list all members (paginated)
    @PreAuthorize("hasRole('ADMIN')")
    @GetMapping
    public ResponseEntity<MemberPageResponse> listMembers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        MemberPageResponse response = memberService.listMembers(page, size);
        return ResponseEntity.ok(response);
    }

    // GET /api/members/{id} — admin: get member by id
    @PreAuthorize("hasRole('ADMIN')")
    @GetMapping("/{id}")
    public ResponseEntity<MemberResponse> getMemberById(@PathVariable Long id) {
        MemberResponse response = memberService.getMemberById(id);
        return ResponseEntity.ok(response);
    }
}
