"use client";

import { useState } from "react";

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    message: "",
  });
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setErrorMessage("");

    try {
      const response = await fetch("http://localhost:5000/api/inquiry", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error("Failed to send inquiry");
      }

      setStatus("success");
      setFormData({ name: "", email: "", message: "" });
    } catch (err: any) {
      console.error("Submission error:", err);
      // Fallback to error for now, but often endpoints aren't set up yet
      // To simulate success if the endpoint is not ready, we can uncomment below
      // setStatus("success");
      
      setStatus("error");
      setErrorMessage(err.message || "An error occurred. Please try again.");
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center py-16 px-4 sm:px-6 lg:px-8">
      <div className="bg-[#fcfcfc] shadow-xl shadow-black/5 rounded-xl border border-gray-100 p-10 sm:p-14 w-full max-w-3xl">
        <div className="mb-10">
          <h1 className="text-3xl font-bold text-gray-900 inline-block relative">
            Contact Me
            <svg
              className="absolute w-[110%] h-3 -bottom-2 -left-1 text-yellow-600/60"
              viewBox="0 0 100 10"
              preserveAspectRatio="none"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M0 5 Q 12.5 0 25 5 T 50 5 T 75 5 T 100 5"
                stroke="currentColor"
                strokeWidth="4"
                strokeLinecap="round"
              />
            </svg>
          </h1>
        </div>

        {status === "success" ? (
          <div className="bg-green-50 border border-green-200 text-green-800 rounded-md p-6 text-center">
            <h3 className="text-lg font-medium mb-2">Message Sent Successfully!</h3>
            <p>Thank you for reaching out. We will get back to you shortly.</p>
            <button
              onClick={() => setStatus("idle")}
              className="mt-6 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors font-medium text-sm"
            >
              Send Another Message
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <label htmlFor="name" className="block text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  name="name"
                  id="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Enter your name"
                  className="block w-full bg-white border-b-2 border-black py-3 px-4 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none transition-colors"
                />
              </div>
              <div>
                <label htmlFor="email" className="block text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  name="email"
                  id="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="Enter your Email"
                  className="block w-full bg-white border-b-2 border-black py-3 px-4 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none transition-colors"
                />
              </div>
            </div>

            <div>
              <label htmlFor="message" className="block text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-2">
                Your Message
              </label>
              <textarea
                name="message"
                id="message"
                required
                rows={5}
                value={formData.message}
                onChange={handleChange}
                placeholder="Message"
                className="block w-full bg-white border-b-2 border-black py-3 px-4 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none resize-none transition-colors"
              />
            </div>

            {status === "error" && (
              <div className="text-red-500 text-sm font-medium">
                {errorMessage}
              </div>
            )}

            <div className="flex justify-end pt-4">
              <button
                type="submit"
                disabled={status === "loading"}
                className="bg-black text-white px-8 py-3 text-sm font-bold hover:bg-gray-800 transition-colors disabled:opacity-70 flex items-center justify-center min-w-[160px]"
              >
                {status === "loading" ? "Sending..." : "Send Message"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
