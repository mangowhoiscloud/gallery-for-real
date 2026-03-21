'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { getProfile, updateProfile } from '@/lib/api';
import { isAuthenticated, clearCredentials } from '@/lib/auth';
import { useToast } from '@/components/ToastProvider';
import type { Member, UpdateProfilePayload } from '@/lib/types';

export default function ProfilePage() {
  const router = useRouter();
  const { toast } = useToast();

  const [profile, setProfile] = useState<Member | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Edit form state
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login?redirect=/profile');
      return;
    }
    getProfile()
      .then((data) => {
        setProfile(data);
        setName(data.name);
        setPhone(data.phone ?? '');
        setAddress(data.address ?? '');
      })
      .catch(() => {
        toast({ title: 'Failed to load profile', variant: 'error' });
      })
      .finally(() => setIsLoading(false));
  }, [router, toast]);

  function handleEdit() {
    if (!profile) return;
    setName(profile.name);
    setPhone(profile.phone ?? '');
    setAddress(profile.address ?? '');
    setIsEditing(true);
  }

  function handleCancel() {
    setIsEditing(false);
  }

  async function handleSave() {
    setIsSaving(true);
    const payload: UpdateProfilePayload = {
      name: name.trim() || undefined,
      phone: phone.trim() || undefined,
      address: address.trim() || undefined,
    };
    try {
      const updated = await updateProfile(payload);
      setProfile(updated);
      setIsEditing(false);
      toast({ title: 'Profile updated successfully', variant: 'success' });
    } catch {
      toast({ title: 'Failed to update profile', variant: 'error' });
    } finally {
      setIsSaving(false);
    }
  }

  function handleLogout() {
    clearCredentials();
    toast({ title: 'Logged out successfully', variant: 'success' });
    router.push('/');
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
        </div>
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">My Profile</h1>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Account Information
          </h2>
          {!isEditing && (
            <button
              onClick={handleEdit}
              className="px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 border border-blue-600 dark:border-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
            >
              Edit Profile
            </button>
          )}
        </div>

        <div className="space-y-4">
          {/* Email — always read-only */}
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Email
            </label>
            <p className="text-gray-900 dark:text-white">{profile.email}</p>
          </div>

          {/* Name */}
          <div>
            <label
              htmlFor="name"
              className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1"
            >
              Name
            </label>
            {isEditing ? (
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            ) : (
              <p className="text-gray-900 dark:text-white">{profile.name}</p>
            )}
          </div>

          {/* Phone */}
          <div>
            <label
              htmlFor="phone"
              className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1"
            >
              Phone
            </label>
            {isEditing ? (
              <input
                id="phone"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="Optional"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            ) : (
              <p className="text-gray-900 dark:text-white">{profile.phone ?? '—'}</p>
            )}
          </div>

          {/* Address */}
          <div>
            <label
              htmlFor="address"
              className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1"
            >
              Address
            </label>
            {isEditing ? (
              <textarea
                id="address"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                rows={2}
                placeholder="Optional"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            ) : (
              <p className="text-gray-900 dark:text-white">{profile.address ?? '—'}</p>
            )}
          </div>
        </div>

        {isEditing && (
          <div className="flex gap-3 mt-6">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? 'Saving…' : 'Save'}
            </button>
            <button
              onClick={handleCancel}
              disabled={isSaving}
              className="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Link
          href="/orders"
          className="flex-1 text-center px-6 py-3 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white font-medium rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          My Orders
        </Link>
        <button
          onClick={handleLogout}
          className="flex-1 px-6 py-3 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-colors"
        >
          Logout
        </button>
      </div>
    </div>
  );
}
