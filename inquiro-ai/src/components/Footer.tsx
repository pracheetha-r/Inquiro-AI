import { AtSign, Share2, SquareTerminal } from "lucide-react";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-[#f4f4f4] border-t border-gray-200 py-6 px-8 flex items-center justify-between mt-auto">
      <div className="flex flex-col">
        <span className="font-bold text-sm tracking-tight mb-1">INQUIRO AI</span>
        <span className="text-xs text-gray-500">© 2024 INQUIRO AI. All rights reserved.</span>
      </div>

      <div className="flex items-center gap-8 text-sm text-gray-500 font-medium">
        <Link href="#" className="hover:text-black transition-colors">Privacy Policy</Link>
        <Link href="#" className="hover:text-black transition-colors">Terms of Service</Link>
        <Link href="#" className="hover:text-black transition-colors">Security</Link>
      </div>

      <div className="flex items-center gap-4">
        <button className="p-2 border border-gray-300 rounded-md hover:bg-white bg-transparent transition-colors">
          <AtSign className="w-4 h-4 text-gray-600" />
        </button>
        <button className="p-2 border border-gray-300 rounded-md hover:bg-white bg-transparent transition-colors">
          <Share2 className="w-4 h-4 text-gray-600" />
        </button>
        <button className="p-2 border border-gray-300 rounded-md hover:bg-white bg-transparent transition-colors">
          <SquareTerminal className="w-4 h-4 text-gray-600" />
        </button>
      </div>
    </footer>
  );
}
