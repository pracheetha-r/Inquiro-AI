"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="flex items-center justify-between py-4 px-8 bg-white border-b border-gray-100 sticky top-0 z-10">
      <div className="flex items-center gap-3">
        {/* Abstract Logo mark from the image (a small dash/line) */}
        <div className="w-5 h-[2px] bg-gray-300"></div>
        <span className="font-bold text-xl tracking-tight">INQUIRO AI</span>
      </div>

      <nav className="flex items-center gap-8">
        <Link 
          href="/" 
          className={`text-sm font-medium ${pathname === "/" ? "text-black border-b-2 border-black pb-1" : "text-gray-500 hover:text-black pb-1"}`}
        >
          Home
        </Link>
        <Link 
          href="/contact" 
          className={`text-sm font-medium ${pathname === "/contact" ? "text-black border-b-2 border-black pb-1" : "text-gray-500 hover:text-black pb-1"}`}
        >
          Contact
        </Link>
      </nav>

      <button className="bg-black text-white px-6 py-2 rounded-md text-sm font-medium hover:bg-gray-800 transition-colors">
        Get Started
      </button>
    </header>
  );
}
