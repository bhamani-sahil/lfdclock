import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Ship, Clock, Bell, FileText, ArrowRight, CheckCircle } from 'lucide-react';

export const LandingPage = () => {
  const features = [
    {
      icon: FileText,
      title: 'Smart Email Parsing',
      description: 'Forward your freight notifications and we\'ll automatically extract container data using AI.'
    },
    {
      icon: Clock,
      title: 'Real-Time Tracking',
      description: 'Visual traffic light system shows exactly how much time you have before LFD expires.'
    },
    {
      icon: Bell,
      title: 'Automated Alerts',
      description: 'SMS notifications at 48h, 24h, 12h, and 6h intervals. Customize what you receive.'
    }
  ];

  const benefits = [
    'Avoid costly demurrage charges',
    'Never miss a pickup deadline',
    'Centralized shipment visibility',
    'AI-powered document parsing'
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 bg-primary rounded-sm flex items-center justify-center">
                <Ship className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight">LFD Clock</span>
            </div>
            <div className="flex items-center gap-3">
              <Link to="/login">
                <Button variant="ghost" data-testid="nav-login-btn">
                  Sign In
                </Button>
              </Link>
              <Link to="/signup">
                <Button className="btn-industrial" data-testid="nav-signup-btn">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 lg:py-32 overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-10"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1769144256207-bc4bb75b29db?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2MjJ8MHwxfHNlYXJjaHwzfHxjb250YWluZXIlMjBzaGlwJTIwYWVyaWFsJTIwb2NlYW4lMjBsb2dpc3RpY3N8ZW58MHx8fHwxNzczMTg2MTUyfDA&ixlib=rb-4.1.0&q=85')`
          }}
        />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-amber-100 text-amber-800 rounded-sm text-sm font-medium mb-6">
              <Clock className="w-4 h-4" />
              Never miss a Last Free Day again
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 mb-6">
              STOP PAYING
              <br />
              <span className="text-amber-500">DEMURRAGE</span>
            </h1>
            <p className="text-lg sm:text-xl text-slate-600 mb-8 max-w-2xl">
              LFD Clock automatically tracks your container Last Free Days and sends 
              SMS alerts before deadlines hit. Forward your shipping emails and let 
              our AI handle the rest.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/signup">
                <Button 
                  size="lg" 
                  className="h-12 px-8 btn-industrial text-base"
                  data-testid="hero-cta-btn"
                >
                  Start Free Trial
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link to="/login">
                <Button 
                  variant="outline" 
                  size="lg" 
                  className="h-12 px-8 border-2 text-base"
                >
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 mb-4">
              How It Works
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Three simple steps to automated LFD tracking
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="bg-slate-50 border border-slate-200 rounded-sm p-6 hover:border-slate-300 transition-colors"
              >
                <div className="w-12 h-12 bg-primary rounded-sm flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-slate-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Traffic Light Demo Section */}
      <section className="py-20 bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold tracking-tight mb-6">
                Visual Status at a Glance
              </h2>
              <p className="text-lg text-slate-300 mb-8">
                Our traffic light system gives you instant visibility into which 
                containers need immediate attention. No more spreadsheets, no more 
                missed deadlines.
              </p>
              <div className="space-y-4">
                {benefits.map((benefit, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />
                    <span>{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-slate-800 rounded-sm p-6 border border-slate-700">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-slate-900 rounded-sm border-l-4 border-emerald-500">
                  <div>
                    <code className="text-sm text-slate-400">MSCU1234567</code>
                    <p className="text-white font-medium">MSC Aurora</p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 bg-emerald-500 rounded-full" style={{ boxShadow: '0 0 8px #10B981' }} />
                      <span className="text-emerald-400 font-mono">72h</span>
                    </div>
                    <span className="text-xs text-slate-500">Safe</span>
                  </div>
                </div>
                <div className="flex items-center justify-between p-4 bg-slate-900 rounded-sm border-l-4 border-amber-500">
                  <div>
                    <code className="text-sm text-slate-400">CMAU7654321</code>
                    <p className="text-white font-medium">CMA CGM Marco</p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 bg-amber-500 rounded-full" style={{ boxShadow: '0 0 8px #F59E0B' }} />
                      <span className="text-amber-400 font-mono">36h</span>
                    </div>
                    <span className="text-xs text-slate-500">Warning</span>
                  </div>
                </div>
                <div className="flex items-center justify-between p-4 bg-slate-900 rounded-sm border-l-4 border-red-500">
                  <div>
                    <code className="text-sm text-slate-400">MAEU9876543</code>
                    <p className="text-white font-medium">Maersk Edmonton</p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 bg-red-500 rounded-full traffic-light-pulse" style={{ boxShadow: '0 0 8px #EF4444' }} />
                      <span className="text-red-400 font-mono">6h</span>
                    </div>
                    <span className="text-xs text-slate-500">Critical</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-amber-500">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white mb-4">
            Ready to Stop Paying Demurrage?
          </h2>
          <p className="text-lg text-amber-100 mb-8">
            Join freight forwarders who are saving thousands with automated LFD tracking.
          </p>
          <Link to="/signup">
            <Button 
              size="lg" 
              className="h-12 px-8 bg-slate-900 hover:bg-slate-800 text-white btn-industrial text-base"
              data-testid="footer-cta-btn"
            >
              Get Started Free
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-slate-800 rounded-sm flex items-center justify-center">
                <Ship className="w-4 h-4 text-slate-400" />
              </div>
              <span className="font-bold text-white">LFD Clock</span>
            </div>
            <div className="flex items-center gap-6 text-sm">
              <Link to="/privacy" className="hover:text-white transition-colors">
                Privacy Policy
              </Link>
              <Link to="/terms" className="hover:text-white transition-colors">
                Terms of Service
              </Link>
              <a href="mailto:support@lfdclock.com" className="hover:text-white transition-colors">
                Contact
              </a>
            </div>
            <p className="text-sm">
              © 2026 LFD Clock. Built for freight forwarders.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
