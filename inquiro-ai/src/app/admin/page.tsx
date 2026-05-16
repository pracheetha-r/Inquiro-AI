"use client";

import { useEffect, useState } from "react";
import { RefreshCcw, Building2, Mail, Clock, Sparkles } from "lucide-react";

interface Inquiry {
  id: string;
  name: string;
  email: string;
  company?: string;
  message: string;
  service?: string;
  ai_category: string;
  ai_summary: string;
  created_at: string;
}

export default function AdminDashboard() {
  const [inquiries, setInquiries] = useState<Inquiry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchInquiries = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("http://localhost:5000/api/inquiries");
      if (!response.ok) {
        throw new Error("Failed to fetch inquiries");
      }
      const data = await response.json();
      
      // If supabase is not configured, API might return an error object inside 500
      if (data.error) {
         throw new Error(data.error);
      }
      
      setInquiries(Array.isArray(data) ? data : []);
    } catch (err: any) {
      console.error(err);
      setError("Could not load inquiries. Make sure the Flask backend is running on port 5000 and Supabase is configured.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInquiries();
  }, []);

  // Helper function to render colored badges based on category
  const getCategoryBadge = (category: string) => {
    const colors: Record<string, string> = {
      "Web Development": "bg-blue-100 text-blue-800 border-blue-200",
      "Mobile App": "bg-purple-100 text-purple-800 border-purple-200",
      "Marketing": "bg-green-100 text-green-800 border-green-200",
      "SEO": "bg-orange-100 text-orange-800 border-orange-200",
      "General": "bg-gray-100 text-gray-800 border-gray-200",
    };
    
    // Default to gray if not explicitly mapped
    const colorClass = colors[category] || "bg-indigo-100 text-indigo-800 border-indigo-200";
    
    return (
      <span className={`px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider rounded-full border ${colorClass} flex items-center gap-1 w-fit`}>
        <Sparkles className="w-3 h-3" />
        {category}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return "Just now";
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    }).format(date);
  };

  return (
    <div className="flex-1 bg-[#f8f9fa] p-6 md:p-12">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Admin Dashboard</h1>
            <p className="text-gray-500 mt-1 text-sm">Manage and view AI-analyzed client inquiries.</p>
          </div>
          <button 
            onClick={fetchInquiries}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-md shadow-sm hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700 disabled:opacity-50"
          >
            <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh Data
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-8 text-sm">
            {error}
          </div>
        )}

        {loading && !inquiries.length ? (
          <div className="flex justify-center items-center py-20">
            <RefreshCcw className="w-8 h-8 animate-spin text-gray-400" />
          </div>
        ) : !loading && inquiries.length === 0 && !error ? (
          <div className="bg-white border border-gray-200 rounded-xl p-12 text-center shadow-sm">
            <h3 className="text-lg font-medium text-gray-900 mb-2">No inquiries yet</h3>
            <p className="text-gray-500 text-sm">When clients submit the contact form, they will appear here.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {inquiries.map((inq) => (
              <div key={inq.id || inq.created_at} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow flex flex-col h-full">
                {/* Header info */}
                <div className="p-6 border-b border-gray-100 flex-1">
                  <div className="flex justify-between items-start mb-4 gap-4">
                    <h3 className="text-lg font-bold text-gray-900 line-clamp-1">{inq.name}</h3>
                    {getCategoryBadge(inq.ai_category || "General")}
                  </div>
                  
                  <div className="space-y-2 mb-6 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-gray-400" />
                      <a href={`mailto:${inq.email}`} className="hover:text-black hover:underline truncate">{inq.email}</a>
                    </div>
                    {inq.company && (
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-gray-400" />
                        <span className="truncate">{inq.company}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <Clock className="w-4 h-4" />
                      <span>{formatDate(inq.created_at)}</span>
                    </div>
                  </div>

                  {/* AI Summary Block */}
                  <div className="bg-indigo-50/50 border border-indigo-100 rounded-lg p-4 mb-4">
                    <h4 className="text-xs font-bold text-indigo-800 uppercase tracking-wider mb-1 flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> AI Summary
                    </h4>
                    <p className="text-sm text-indigo-900 font-medium leading-relaxed">{inq.ai_summary || "No summary available."}</p>
                  </div>
                  
                  {/* Original Message */}
                  <div>
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Original Message</h4>
                    <p className="text-sm text-gray-600 whitespace-pre-wrap">{inq.message}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
