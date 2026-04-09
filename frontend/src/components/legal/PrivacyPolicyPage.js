import React from 'react';
import { Link } from 'react-router-dom';
import { Ship, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export const PrivacyPolicyPage = () => {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-9 h-9 bg-primary rounded-sm flex items-center justify-center">
                <Ship className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight">LFD Clock</span>
            </Link>
            <Link to="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-3xl font-bold mb-8">Privacy Policy</h1>
        
        <div className="prose prose-slate max-w-none">
          <p className="text-muted-foreground mb-6">Last updated: March 2026</p>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">1. Information We Collect</h2>
            <p className="text-slate-600 mb-4">
              LFD Clock ("we", "our", or "us") collects the following information to provide our container tracking and notification services:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li><strong>Account Information:</strong> Email address, company name, phone number, and password (encrypted)</li>
              <li><strong>Shipment Data:</strong> Container numbers, vessel names, carrier information, arrival dates, and Last Free Day (LFD) dates extracted from documents you provide</li>
              <li><strong>Communication Data:</strong> SMS notification logs and email metadata</li>
              <li><strong>Usage Data:</strong> Login times, feature usage, and interaction with our platform</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">2. How We Use Your Information</h2>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>To provide LFD tracking and SMS alert services</li>
              <li>To parse shipping documents using AI and extract relevant data</li>
              <li>To send notifications about upcoming container deadlines</li>
              <li>To improve our services and develop new features</li>
              <li>To communicate with you about your account</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">3. Data Processing & Third Parties</h2>
            <p className="text-slate-600 mb-4">We use the following third-party services to operate LFD Clock:</p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li><strong>Postmark:</strong> Receives and processes inbound emails. Emails are retained per their data retention policy.</li>
              <li><strong>Google Gemini AI:</strong> Parses shipping documents to extract data. Documents are processed but not stored by Google.</li>
              <li><strong>Twilio:</strong> Sends SMS notifications. Message logs are retained per Twilio's compliance requirements.</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">4. Data Security</h2>
            <p className="text-slate-600 mb-4">We implement security measures to protect your data:</p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>Passwords are encrypted using industry-standard hashing (bcrypt)</li>
              <li>PDF documents are processed in memory and immediately deleted after parsing</li>
              <li>We do not store your original shipping documents</li>
              <li>Access to data is restricted to authorized personnel only</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">5. Data Retention</h2>
            <p className="text-slate-600">
              We retain your account and shipment data for as long as your account is active. You may request deletion of your data at any time by contacting us. Upon account deletion, we will remove your personal data within 30 days.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">6. Your Rights</h2>
            <p className="text-slate-600 mb-4">You have the right to:</p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>Access your personal data</li>
              <li>Correct inaccurate data</li>
              <li>Request deletion of your data</li>
              <li>Export your data</li>
              <li>Opt out of marketing communications</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">7. Contact Us</h2>
            <p className="text-slate-600">
              If you have questions about this Privacy Policy or your data, please contact us at:
              <br /><br />
              <strong>Email:</strong> privacy@lfdclock.com
              <br />
              <strong>Address:</strong> Calgary, Alberta, Canada
            </p>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-8 mt-12">
        <div className="max-w-4xl mx-auto px-4 text-center text-sm text-muted-foreground">
          © 2026 LFD Clock. All rights reserved.
        </div>
      </footer>
    </div>
  );
};
