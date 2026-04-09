import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Anchor, ArrowRight, Loader2, Copy, Check, Mail } from 'lucide-react';
import { toast } from 'sonner';

export const SignupPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [forwardingEmail, setForwardingEmail] = useState('');
  const [copied, setCopied] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const user = await signup(email, password, companyName, phone);
      setForwardingEmail(user.inbound_email || user.forwarding_email);
      setShowOnboarding(true);
      toast.success('Account created successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  const copyEmail = () => {
    navigator.clipboard.writeText(forwardingEmail);
    setCopied(true);
    toast.success('Inbound email copied!');
    setTimeout(() => setCopied(false), 2000);
  };

  if (showOnboarding) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8 bg-[#FAF7F2]">
        <Card className="w-full max-w-lg shadow-lg border-[#E8E2D9] bg-white">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-[#FF4F00] rounded-lg flex items-center justify-center">
                <Check className="w-8 h-8 text-white" />
              </div>
            </div>
            <CardTitle className="text-2xl font-bold tracking-tight">
              You're All Set!
            </CardTitle>
            <CardDescription className="text-base">
              Your unique inbound email is ready
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="bg-[#FF4F00]/10 border-2 border-[#FF4F00]/30 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Mail className="w-4 h-4 text-[#FF4F00]" />
                <span className="text-sm font-medium text-[#FF4F00]">
                  Your Inbound Email
                </span>
              </div>
              <div className="flex items-center gap-2">
                <code className="flex-1 font-mono text-lg bg-white px-3 py-2 rounded-lg border border-[#FF4F00]/20 text-[#1A1A1A]">
                  {forwardingEmail}
                </code>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={copyEmail}
                  className="shrink-0 border-[#FF4F00]/30 hover:bg-[#FF4F00]/10"
                  data-testid="copy-email-btn"
                >
                  {copied ? (
                    <Check className="w-4 h-4 text-[#FF4F00]" />
                  ) : (
                    <Copy className="w-4 h-4 text-[#FF4F00]" />
                  )}
                </Button>
              </div>
            </div>

            <div className="bg-[#F5F1E8] border border-[#E8E2D9] rounded-lg p-4">
              <h4 className="font-medium text-[#1A1A1A] mb-2">How carriers send you LFD notices:</h4>
              <ol className="text-sm text-[#666666] space-y-2 list-decimal list-inside">
                <li>Give this email to your shipping lines & forwarders</li>
                <li>They email PDF arrival notices to this address</li>
                <li>We parse the LFD and send you instant SMS alerts</li>
              </ol>
            </div>

            <Button
              onClick={() => navigate('/dashboard')}
              className="w-full h-11 btn-accent-glow rounded-lg"
              data-testid="go-to-dashboard-btn"
            >
              Go to Dashboard
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      {/* Left side - Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-[#FAF7F2]">
        <Card className="w-full max-w-md shadow-lg border-[#E8E2D9] bg-white">
          <CardHeader className="space-y-1 text-center">
            <div className="flex justify-center mb-4">
              <div className="w-12 h-12 bg-[#FF4F00] rounded-lg flex items-center justify-center">
                <Anchor className="w-6 h-6 text-white" />
              </div>
            </div>
            <CardTitle className="text-2xl font-bold tracking-tight">
              Create your account
            </CardTitle>
            <CardDescription>
              Start tracking your shipment LFDs today
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="companyName">Company Name</Label>
                <Input
                  id="companyName"
                  type="text"
                  placeholder="Acme Logistics"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  required
                  data-testid="signup-company-input"
                  className="h-11 bg-white border-2 border-[#E8E2D9] focus:border-[#FF4F00] focus:ring-[#FF4F00]/20"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  data-testid="signup-email-input"
                  className="h-11 bg-white border-2 border-[#E8E2D9] focus:border-[#FF4F00] focus:ring-[#FF4F00]/20"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number (for SMS alerts)</Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="+1 555 000 0000"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  required
                  data-testid="signup-phone-input"
                  className="h-11 bg-white border-2 border-[#E8E2D9] focus:border-[#FF4F00] focus:ring-[#FF4F00]/20"
                />
                <p className="text-xs text-muted-foreground">Include country code (e.g., +1 for US/Canada)</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  data-testid="signup-password-input"
                  className="h-11 bg-white border-2 border-[#E8E2D9] focus:border-[#FF4F00] focus:ring-[#FF4F00]/20"
                />
              </div>
              <Button
                type="submit"
                className="w-full h-11 btn-accent-glow rounded-lg"
                disabled={loading}
                data-testid="signup-submit-btn"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    Create Account
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </>
                )}
              </Button>
            </form>

            <div className="mt-6 text-center text-sm">
              <span className="text-muted-foreground">Already have an account? </span>
              <Link 
                to="/login" 
                className="text-[#FF4F00] font-medium hover:underline"
                data-testid="login-link"
              >
                Sign in
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Right side - Image */}
      <div 
        className="hidden lg:flex lg:w-1/2 relative bg-cover bg-center"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1769144256207-bc4bb75b29db?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2MjJ8MHwxfHNlYXJjaHwzfHxjb250YWluZXIlMjBzaGlwJTIwYWVyaWFsJTIwb2NlYW4lMjBsb2dpc3RpY3N8ZW58MHx8fHwxNzczMTg2MTUyfDA&ixlib=rb-4.1.0&q=85')`
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-[#FF4F00]/80 to-slate-900/90" />
        <div className="relative z-10 flex flex-col justify-end p-12 text-white">
          <h2 className="text-3xl font-bold mb-4">Stay Ahead of Demurrage</h2>
          <p className="text-white/80 text-lg">
            Get automatic SMS alerts at 48h, 24h, 12h, and 6h before your container's Last Free Day expires.
          </p>
        </div>
      </div>
    </div>
  );
};
