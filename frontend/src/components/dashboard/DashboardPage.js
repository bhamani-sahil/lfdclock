import React, { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { TrafficLight, StatusBadge } from '@/components/TrafficLight';
import { CountdownTimer, CompactCountdown } from '@/components/CountdownTimer';
import { toast } from 'sonner';
import {
  Ship,
  Plus,
  Settings,
  LogOut,
  User,
  Mail,
  Copy,
  Check,
  RefreshCw,
  Trash2,
  FileText,
  Bell,
  AlertTriangle,
  Clock,
  Package,
  Loader2,
  Sparkles,
  Smartphone,
  Send,
  Zap
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const DashboardPage = () => {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [shipments, setShipments] = useState([]);
  const [stats, setStats] = useState({ total: 0, safe: 0, warning: 0, critical: 0, expired: 0 });
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [seedingDemo, setSeedingDemo] = useState(false);

  const isSettingsPage = location.pathname === '/settings';

  useEffect(() => {
    if (token) {
      fetchData();
    }
  }, [token]);

  const fetchData = async () => {
    try {
      const [shipmentsRes, statsRes] = await Promise.all([
        axios.get(`${API}/shipments`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/shipments/stats`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setShipments(shipmentsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Failed to load shipments');
    } finally {
      setLoading(false);
    }
  };

  const copyEmail = () => {
    navigator.clipboard.writeText(user?.forwarding_email || '');
    setCopied(true);
    toast.success('Email copied!');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const seedDemoData = async () => {
    setSeedingDemo(true);
    try {
      await axios.post(`${API}/demo/seed`, {}, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Demo shipments created!');
      fetchData();
    } catch (error) {
      toast.error('Failed to create demo data');
    } finally {
      setSeedingDemo(false);
    }
  };

  const deleteShipment = async (id) => {
    try {
      await axios.delete(`${API}/shipments/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('Shipment deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete shipment');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/dashboard" className="flex items-center gap-2">
              <div className="w-9 h-9 bg-primary rounded-sm flex items-center justify-center">
                <Ship className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight">LFD Clock</span>
            </Link>

            <div className="flex items-center gap-4">
              {/* Forwarding Email */}
              <div className="hidden md:flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-sm">
                <Mail className="w-4 h-4 text-muted-foreground" />
                <code className="text-sm font-mono">{user?.forwarding_email}</code>
                <button
                  onClick={copyEmail}
                  className="p-1 hover:bg-slate-200 rounded-sm transition-colors"
                  data-testid="copy-fwd-email-btn"
                >
                  {copied ? (
                    <Check className="w-3.5 h-3.5 text-emerald-500" />
                  ) : (
                    <Copy className="w-3.5 h-3.5 text-muted-foreground" />
                  )}
                </button>
              </div>

              {/* User Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" data-testid="user-menu-btn">
                    <User className="w-5 h-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <div className="px-2 py-1.5">
                    <p className="font-medium">{user?.company_name}</p>
                    <p className="text-sm text-muted-foreground">{user?.email}</p>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate('/settings')} data-testid="settings-menu-item">
                    <Settings className="w-4 h-4 mr-2" />
                    Notification Settings
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} data-testid="logout-menu-item">
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isSettingsPage ? (
          <SettingsContent token={token} />
        ) : (
          <>
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Live Shipments</h1>
                <p className="text-muted-foreground">Track your container Last Free Days</p>
              </div>
              <div className="flex gap-3">
                <TestEmailSMSDialog token={token} onSuccess={fetchData} />
                <Button
                  variant="outline"
                  onClick={seedDemoData}
                  disabled={seedingDemo}
                  data-testid="seed-demo-btn"
                >
                  {seedingDemo ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4 mr-2" />
                  )}
                  Load Demo Data
                </Button>
                <AddShipmentDialog 
                  open={addDialogOpen} 
                  onOpenChange={setAddDialogOpen}
                  token={token}
                  onSuccess={fetchData}
                />
              </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
              <StatCard label="Total" value={stats.total} icon={Package} />
              <StatCard label="Safe" value={stats.safe} icon={Check} variant="safe" />
              <StatCard label="Warning" value={stats.warning} icon={Clock} variant="warning" />
              <StatCard label="Critical" value={stats.critical} icon={AlertTriangle} variant="critical" />
              <StatCard label="Expired" value={stats.expired} icon={AlertTriangle} variant="expired" />
            </div>

            {/* Shipments Grid */}
            {loading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
              </div>
            ) : shipments.length === 0 ? (
              <EmptyState onSeedDemo={seedDemoData} seedingDemo={seedingDemo} />
            ) : (
              <div className="space-y-4">
                {shipments.map((shipment) => (
                  <ShipmentCard 
                    key={shipment.id} 
                    shipment={shipment} 
                    onDelete={() => deleteShipment(shipment.id)}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

const StatCard = ({ label, value, icon: Icon, variant }) => {
  const variants = {
    safe: 'border-l-emerald-500 bg-emerald-50',
    warning: 'border-l-amber-500 bg-amber-50',
    critical: 'border-l-red-500 bg-red-50',
    expired: 'border-l-slate-400 bg-slate-100',
    default: 'border-l-slate-300'
  };

  return (
    <Card className={`border-l-4 ${variants[variant] || variants.default}`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold font-mono">{value}</p>
          </div>
          <Icon className="w-5 h-5 text-muted-foreground" />
        </div>
      </CardContent>
    </Card>
  );
};

const ShipmentCard = ({ shipment, onDelete }) => {
  const statusBorderColors = {
    safe: 'border-l-emerald-500',
    warning: 'border-l-amber-500',
    critical: 'border-l-red-500',
    expired: 'border-l-slate-400'
  };

  return (
    <Card 
      className={`border-l-4 ${statusBorderColors[shipment.status] || 'border-l-slate-300'} hover:shadow-md transition-shadow`}
      data-testid={`shipment-card-${shipment.container_number}`}
    >
      <CardContent className="p-4 md:p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Left: Container Info */}
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <code className="text-lg font-mono font-bold">{shipment.container_number}</code>
              <StatusBadge status={shipment.status}>
                {shipment.status.charAt(0).toUpperCase() + shipment.status.slice(1)}
              </StatusBadge>
              {shipment.source !== 'manual' && (
                <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-sm">
                  {shipment.source === 'email' ? 'Email Parsed' : 'Demo'}
                </span>
              )}
            </div>
            <p className="text-slate-600 font-medium">{shipment.vessel_name}</p>
            <p className="text-sm text-muted-foreground">
              Arrival: {new Date(shipment.arrival_date).toLocaleDateString()}
            </p>
          </div>

          {/* Center: Countdown */}
          <div className="flex-1 flex flex-col items-center">
            <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wide">Time Remaining</p>
            <CountdownTimer targetDate={shipment.last_free_day} />
          </div>

          {/* Right: LFD Date & Actions */}
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Last Free Day</p>
              <p className="font-mono font-medium">
                {new Date(shipment.last_free_day).toLocaleDateString()}
              </p>
              <p className="text-xs text-muted-foreground">
                {new Date(shipment.last_free_day).toLocaleTimeString()}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onDelete}
              className="text-muted-foreground hover:text-red-600"
              data-testid={`delete-shipment-${shipment.container_number}`}
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const EmptyState = ({ onSeedDemo, seedingDemo }) => (
  <Card className="border-dashed">
    <CardContent className="py-16 text-center">
      <div className="w-16 h-16 bg-slate-100 rounded-sm flex items-center justify-center mx-auto mb-4">
        <Package className="w-8 h-8 text-slate-400" />
      </div>
      <h3 className="text-xl font-bold mb-2">No Shipments Yet</h3>
      <p className="text-muted-foreground mb-6 max-w-md mx-auto">
        Forward your freight notifications to your unique email address, or add shipments manually.
      </p>
      <Button onClick={onSeedDemo} disabled={seedingDemo} data-testid="empty-seed-demo-btn">
        {seedingDemo ? (
          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
        ) : (
          <Sparkles className="w-4 h-4 mr-2" />
        )}
        Load Demo Shipments
      </Button>
    </CardContent>
  </Card>
);

const AddShipmentDialog = ({ open, onOpenChange, token, onSuccess }) => {
  const [formData, setFormData] = useState({
    container_number: '',
    vessel_name: '',
    arrival_date: '',
    last_free_day: '',
    notes: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Convert local datetime to ISO string
      const payload = {
        ...formData,
        arrival_date: new Date(formData.arrival_date).toISOString(),
        last_free_day: new Date(formData.last_free_day).toISOString()
      };

      await axios.post(`${API}/shipments`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Shipment added successfully');
      onOpenChange(false);
      setFormData({
        container_number: '',
        vessel_name: '',
        arrival_date: '',
        last_free_day: '',
        notes: ''
      });
      onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add shipment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button className="btn-industrial" data-testid="add-shipment-btn">
          <Plus className="w-4 h-4 mr-2" />
          Add Shipment
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add New Shipment</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="container_number">Container Number</Label>
            <Input
              id="container_number"
              placeholder="e.g. MSCU1234567"
              value={formData.container_number}
              onChange={(e) => setFormData({ ...formData, container_number: e.target.value })}
              required
              data-testid="add-container-input"
              className="font-mono"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="vessel_name">Vessel Name</Label>
            <Input
              id="vessel_name"
              placeholder="e.g. MSC Aurora"
              value={formData.vessel_name}
              onChange={(e) => setFormData({ ...formData, vessel_name: e.target.value })}
              required
              data-testid="add-vessel-input"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="arrival_date">Arrival Date</Label>
            <Input
              id="arrival_date"
              type="datetime-local"
              value={formData.arrival_date}
              onChange={(e) => setFormData({ ...formData, arrival_date: e.target.value })}
              required
              data-testid="add-arrival-input"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="last_free_day">Last Free Day (LFD)</Label>
            <Input
              id="last_free_day"
              type="datetime-local"
              value={formData.last_free_day}
              onChange={(e) => setFormData({ ...formData, last_free_day: e.target.value })}
              required
              data-testid="add-lfd-input"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="notes">Notes (Optional)</Label>
            <Input
              id="notes"
              placeholder="Any additional notes..."
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              data-testid="add-notes-input"
            />
          </div>
          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="flex-1 btn-industrial"
              data-testid="add-shipment-submit-btn"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Add Shipment'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

const TestEmailSMSDialog = ({ token, onSuccess }) => {
  const [open, setOpen] = useState(false);
  const [emailContent, setEmailContent] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const sampleEmail = `Subject: Arrival Notice - Container MSCU1234567

Dear Customer,

Your shipment has arrived at the Port of Los Angeles.

Container Number: MSCU1234567
Vessel: MSC AURORA
Arrival Date: March 10, 2026
Last Free Day (LFD): March 15, 2026

Please arrange pickup before the LFD to avoid demurrage charges.

Best regards,
Shipping Line`;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const response = await axios.post(
        `${API}/test/email-sms`,
        {
          email_content: emailContent,
          phone_number: phoneNumber
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setResult(response.data);
      toast.success('SMS sent successfully! Check your phone!');
      onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Test failed');
      setResult({ error: error.response?.data?.detail || 'Test failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="bg-emerald-50 border-emerald-200 text-emerald-700 hover:bg-emerald-100" data-testid="test-sms-btn">
          <Zap className="w-4 h-4 mr-2" />
          Test SMS
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Smartphone className="w-5 h-5 text-emerald-600" />
            Test Email Parse + Real SMS
          </DialogTitle>
          <DialogDescription>
            Paste email content, we'll parse it with AI and send you a REAL SMS!
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="phone">Your Phone Number (with country code)</Label>
            <Input
              id="phone"
              placeholder="+18257607425"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              required
              data-testid="test-phone-input"
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground">Include country code (e.g., +1 for US, +91 for India)</p>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="email_content">Email Content</Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setEmailContent(sampleEmail)}
                className="text-xs"
              >
                Load Sample
              </Button>
            </div>
            <Textarea
              id="email_content"
              placeholder="Paste your shipment email content here..."
              value={emailContent}
              onChange={(e) => setEmailContent(e.target.value)}
              required
              rows={8}
              data-testid="test-email-input"
              className="font-mono text-sm"
            />
          </div>
          
          {result && (
            <div className={`p-4 rounded-sm text-sm ${result.error ? 'bg-red-50 border border-red-200' : 'bg-emerald-50 border border-emerald-200'}`}>
              {result.error ? (
                <p className="text-red-700">{result.error}</p>
              ) : (
                <div className="space-y-2">
                  <p className="text-emerald-700 font-medium flex items-center gap-2">
                    <Check className="w-4 h-4" /> SMS Sent Successfully!
                  </p>
                  <p className="text-emerald-600">Container: {result.parsed_data?.container_number}</p>
                  <p className="text-emerald-600">Sent to: {result.sms?.sent_to}</p>
                  <p className="text-emerald-600 text-xs">Twilio SID: {result.sms?.twilio_sid}</p>
                </div>
              )}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700"
              data-testid="test-sms-submit-btn"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Parse & Send SMS
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

const SettingsContent = ({ token }) => {
  const [settings, setSettings] = useState({
    notify_48h: true,
    notify_24h: true,
    notify_12h: true,
    notify_6h: true
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSettings(response.data);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = async (key, value) => {
    setSaving(true);
    try {
      await axios.put(
        `${API}/settings/notifications`,
        { [key]: value },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSettings(prev => ({ ...prev, [key]: value }));
      toast.success('Settings updated');
    } catch (error) {
      toast.error('Failed to update settings');
    } finally {
      setSaving(false);
    }
  };

  const intervals = [
    { key: 'notify_48h', label: '48 Hours', description: 'Get notified 2 days before LFD expires' },
    { key: 'notify_24h', label: '24 Hours', description: 'Get notified 1 day before LFD expires' },
    { key: 'notify_12h', label: '12 Hours', description: 'Get notified 12 hours before LFD expires' },
    { key: 'notify_6h', label: '6 Hours', description: 'Urgent alert 6 hours before LFD expires' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Notification Settings</h1>
        <p className="text-muted-foreground">Choose when you want to receive SMS alerts</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            SMS Alert Intervals
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {intervals.map((interval) => (
            <div 
              key={interval.key}
              className="flex items-center justify-between py-3 border-b border-slate-100 last:border-0"
            >
              <div>
                <p className="font-medium">{interval.label} Alert</p>
                <p className="text-sm text-muted-foreground">{interval.description}</p>
              </div>
              <Switch
                checked={settings[interval.key]}
                onCheckedChange={(checked) => updateSetting(interval.key, checked)}
                disabled={saving}
                data-testid={`toggle-${interval.key}`}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-sm">
        <div className="flex gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-amber-800">SMS Notifications are Mocked</p>
            <p className="text-sm text-amber-700">
              In this demo, SMS notifications are simulated. In production, these would be sent via Twilio to your registered phone number.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
