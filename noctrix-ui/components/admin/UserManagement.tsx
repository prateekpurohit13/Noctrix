"use client";
import { useState, useEffect, useMemo } from 'react';
import apiClient from '@/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { format } from 'date-fns';
import { Search, UserPlus, Users, Shield, Trash2, Filter, Calendar } from 'lucide-react';

interface User {
  id: number;
  username: string;
  role: 'Admin' | 'Analyst';
  last_login: string | null;
}

function AddUserDialog({ onUserAdded }: { onUserAdded: () => void }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState<'Admin' | 'Analyst'>('Analyst');
    const [isOpen, setIsOpen] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async () => {
        if (!username.trim() || !password.trim()) {
            toast.error('Username and password are required.');
            return;
        }

        try {
            setIsSubmitting(true);
            await apiClient.post('/admin/users', { username: username.trim(), password, role });
            toast.success(`User "${username}" created successfully.`);
            onUserAdded();
            setIsOpen(false);
            setUsername(''); 
            setPassword(''); 
            setRole('Analyst');
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to create user.');
        } finally {
            setIsSubmitting(false);
        }
    };
    
    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <Button className="gap-2 bg-black text-white dark:bg-teal-500 dark:text-black border-none hover:bg-gray-900 dark:hover:bg-teal-600">
                    <UserPlus className="h-4 w-4" />
                    Add New User
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <UserPlus className="h-5 w-5" />
                        Create New User
                    </DialogTitle>
                    <DialogDescription>
                        Add a new user to the system. They will be required to change their password on first login.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-6 py-4">
                    <div className="space-y-2">
                        <Label htmlFor="username">Username</Label>
                        <Input 
                            id="username" 
                            placeholder="Enter username" 
                            value={username} 
                            onChange={(e) => setUsername(e.target.value)} 
                            disabled={isSubmitting}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="password">Initial Password</Label>
                        <Input 
                            id="password" 
                            type="password" 
                            placeholder="Enter temporary password" 
                            value={password} 
                            onChange={(e) => setPassword(e.target.value)} 
                            disabled={isSubmitting}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="role">Role</Label>
                        <Select value={role} onValueChange={(value: 'Admin' | 'Analyst') => setRole(value)} disabled={isSubmitting}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select a role" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="Analyst">
                                    <div className="flex items-center gap-2">
                                        <Users className="h-4 w-4" />
                                        Analyst
                                    </div>
                                </SelectItem>
                                <SelectItem value="Admin">
                                    <div className="flex items-center gap-2">
                                        <Shield className="h-4 w-4" />
                                        Admin
                                    </div>
                                </SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>
                <DialogFooter>
                    <DialogClose asChild>
                        <Button variant="outline" disabled={isSubmitting}>Cancel</Button>
                    </DialogClose>
                    <Button onClick={handleSubmit} disabled={isSubmitting} className="gap-2">
                        {isSubmitting ? (
                            <>
                                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                                Creating...
                            </>
                        ) : (
                            <>
                                <UserPlus className="h-4 w-4" />
                                Create User
                            </>
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

export default function EnhancedUserManagement() {
    const [users, setUsers] = useState<User[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [roleFilter, setRoleFilter] = useState<'all' | 'Admin' | 'Analyst'>('all');
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [isLoading, setIsLoading] = useState(true);

    const fetchUsers = async () => {
        try {
            setIsLoading(true);
            const response = await apiClient.get('/admin/users');
            setUsers(response.data);
        } catch (error) {
            toast.error('Failed to fetch users.');
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const filteredUsers = useMemo(() => {
        return users
            .filter(user => 
                user.username.toLowerCase().includes(searchTerm.toLowerCase())
            )
            .filter(user => 
                roleFilter === 'all' ? true : user.role === roleFilter
            );
    }, [users, searchTerm, roleFilter]);

    const paginatedUsers = useMemo(() => {
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        return filteredUsers.slice(startIndex, endIndex);
    }, [filteredUsers, currentPage, itemsPerPage]);

    const totalPages = Math.ceil(filteredUsers.length / itemsPerPage);

    const handleDelete = async (userId: number, username: string) => {
        if (!confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
            return;
        }
        try {
            await apiClient.delete(`/admin/users/${userId}`);
            toast.success(`User "${username}" deleted successfully.`);
            fetchUsers();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to delete user.');
        }
    };

    const getRoleBadge = (role: 'Admin' | 'Analyst') => {
        return role === 'Admin' ? (
            <Badge variant="default" className="gap-1 bg-orange-500 hover:bg-orange-600">
                <Shield className="h-3 w-3" />
                Admin
            </Badge>
        ) : (
            <Badge variant="secondary" className="gap-1">
                <Users className="h-3 w-3" />
                Analyst
            </Badge>
        );
    };

    const userStats = useMemo(() => {
        const total = users.length;
        const admins = users.filter(u => u.role === 'Admin').length;
        const analysts = users.filter(u => u.role === 'Analyst').length;
        const recentLogins = users.filter(u => u.last_login && 
            new Date(u.last_login) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
        ).length;
        
        return { total, admins, analysts, recentLogins };
    }, [users]);

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="p-2 rounded-md bg-primary/10">
                            <Users className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                            <CardTitle>User Management</CardTitle>
                            <CardDescription>Manage system users and their permissions</CardDescription>
                        </div>
                    </div>
                    <AddUserDialog onUserAdded={fetchUsers} />
                </div>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-muted/30 rounded-lg">
                    <div className="text-center">
                        <div className="text-2xl font-bold text-primary">{userStats.total}</div>
                        <div className="text-xs text-muted-foreground">Total Users</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-orange-500">{userStats.admins}</div>
                        <div className="text-xs text-muted-foreground">Admins</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-blue-500">{userStats.analysts}</div>
                        <div className="text-xs text-muted-foreground">Analysts</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-green-500">{userStats.recentLogins}</div>
                        <div className="text-xs text-muted-foreground">Active (7d)</div>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <div className="relative flex-1 max-w-sm">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input 
                            type="search" 
                            placeholder="Search users..." 
                            className="pl-9"
                            value={searchTerm}
                            onChange={(e) => {
                                setSearchTerm(e.target.value);
                                setCurrentPage(1);
                            }}
                        />
                    </div>
                    <Select value={roleFilter} onValueChange={(value: any) => {
                        setRoleFilter(value);
                        setCurrentPage(1);
                    }}>
                        <SelectTrigger className="w-[160px]">
                            <Filter className="h-4 w-4 mr-2" />
                            <SelectValue placeholder="All Roles" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Roles</SelectItem>
                            <SelectItem value="Admin">
                                <div className="flex items-center gap-2">
                                    <Shield className="h-4 w-4" />
                                    Admin
                                </div>
                            </SelectItem>
                            <SelectItem value="Analyst">
                                <div className="flex items-center gap-2">
                                    <Users className="h-4 w-4" />
                                    Analyst
                                </div>
                            </SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <div className="border rounded-lg overflow-hidden">
                    <Table>
                        <TableHeader>
                            <TableRow className="bg-muted/50">
                                <TableHead className="font-semibold">User</TableHead>
                                <TableHead className="font-semibold">Role</TableHead>
                                <TableHead className="font-semibold">Last Login</TableHead>
                                <TableHead className="text-right font-semibold">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading ? (
                                Array.from({ length: itemsPerPage }).map((_, index) => (
                                    <TableRow key={index}>
                                        <TableCell><div className="w-24 h-4 bg-muted animate-pulse rounded" /></TableCell>
                                        <TableCell><div className="w-16 h-4 bg-muted animate-pulse rounded" /></TableCell>
                                        <TableCell><div className="w-32 h-4 bg-muted animate-pulse rounded" /></TableCell>
                                        <TableCell><div className="w-20 h-8 bg-muted animate-pulse rounded ml-auto" /></TableCell>
                                    </TableRow>
                                ))
                            ) : paginatedUsers.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={4} className="h-32 text-center">
                                        <div className="flex flex-col items-center gap-2">
                                            <Users className="h-8 w-8 text-muted-foreground" />
                                            <p className="text-muted-foreground">
                                                {filteredUsers.length === 0 && users.length > 0
                                                    ? "No users match your search criteria"
                                                    : "No users found"
                                                }
                                            </p>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ) : (
                                paginatedUsers.map((user) => (
                                    <TableRow key={user.id} className="hover:bg-muted/30">
                                        <TableCell>
                                            <div className="flex items-center gap-3">
                                                <div className="p-2 rounded-full bg-primary/10">
                                                    <Users className="h-4 w-4 text-primary" />
                                                </div>
                                                <div>
                                                    <div className="font-medium">{user.username}</div>
                                                    <div className="text-xs text-muted-foreground">ID: {user.id}</div>
                                                </div>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            {getRoleBadge(user.role)}
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                <Calendar className="h-4 w-4 text-muted-foreground" />
                                                <span className="text-sm">
                                                    {user.last_login 
                                                        ? format(new Date(user.last_login), 'PPpp') 
                                                        : 'Never logged in'
                                                    }
                                                </span>
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <Button 
                                                variant="destructive" 
                                                size="sm" 
                                                onClick={() => handleDelete(user.id, user.username)}
                                                className="gap-1"
                                            >
                                                <Trash2 className="h-3 w-3" />
                                                Delete
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </div>

                <div className="flex items-center justify-between pt-4 border-t">
                    <div className="text-sm text-muted-foreground">
                        Showing {paginatedUsers.length === 0 ? 0 : (currentPage - 1) * itemsPerPage + 1} to{' '}
                        {Math.min(currentPage * itemsPerPage, filteredUsers.length)} of {filteredUsers.length} users
                    </div>
                    <div className="flex items-center gap-2">
                        <Select value={String(itemsPerPage)} onValueChange={(value) => {
                            setItemsPerPage(Number(value));
                            setCurrentPage(1);
                        }}>
                            <SelectTrigger className="w-[70px]">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="10">10</SelectItem>
                                <SelectItem value="25">25</SelectItem>
                                <SelectItem value="50">50</SelectItem>
                            </SelectContent>
                        </Select>
                        <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))} 
                            disabled={currentPage === 1 || filteredUsers.length === 0}
                        >
                            Previous
                        </Button>
                        <span className="text-sm text-muted-foreground px-2">
                            {filteredUsers.length === 0 ? 0 : currentPage} of {Math.max(1, totalPages)}
                        </span>
                        <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} 
                            disabled={currentPage === totalPages || filteredUsers.length === 0}
                        >
                            Next
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}