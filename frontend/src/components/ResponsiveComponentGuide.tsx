/**
 * MOBILE RESPONSIVE DESIGN BEST PRACTICES GUIDE
 * 
 * This file demonstrates how to build mobile-responsive components
 * using Tailwind CSS with the mobile-first approach.
 */

/*
 * RESPONSIVE BREAKPOINTS
 * 
 * Mobile First Approach:
 * - Default styles apply to all screen sizes
 * - Use sm:, md:, lg:, xl:, 2xl: prefixes to override for larger screens
 * 
 * Tailwind Breakpoints:
 * - sm: @media (min-width: 640px)
 * - md: @media (min-width: 768px)  [tablet]
 * - lg: @media (min-width: 1024px) [desktop]
 * - xl: @media (min-width: 1280px)
 * - 2xl: @media (min-width: 1536px)
 */

/* ============================================================================
   EXAMPLE 1: RESPONSIVE CARD COMPONENT
   ============================================================================ */

export const ResponsiveCard = () => {
  return (
    <div className="
      /* Base mobile styles */
      bg-white dark:bg-gray-900
      rounded-lg
      shadow-sm
      border border-gray-200 dark:border-gray-700
      p-4 sm:p-6 md:p-8
      my-4 sm:my-6 md:my-8
      
      /* Hover effect - only on non-touch devices */
      hover:shadow-md
      transition-shadow duration-200
      
      /* Accessibility */
      focus-within:ring-2 focus-within:ring-blue-500
    ">
      <h2 className="
        text-xl sm:text-2xl md:text-3xl
        font-bold
        mb-2 sm:mb-3 md:mb-4
        text-gray-900 dark:text-white
      ">
        Card Title
      </h2>
      
      <p className="
        text-sm sm:text-base md:text-lg
        text-gray-600 dark:text-gray-400
        leading-relaxed
      ">
        Responsive card content that adapts to screen size.
      </p>
    </div>
  );
};

/* ============================================================================
   EXAMPLE 2: RESPONSIVE GRID LAYOUT
   ============================================================================ */

export const ResponsiveGrid = () => {
  return (
    <div className="
      /* Grid with responsive columns */
      grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4
      
      /* Responsive gap spacing */
      gap-4 sm:gap-5 md:gap-6 lg:gap-8
      
      /* Container padding */
      px-4 sm:px-6 md:px-8
      py-6 sm:py-8 md:py-12
      
      /* Max width constraint */
      max-w-7xl mx-auto
    ">
      {/* Grid items will automatically reflow based on screen size */}
    </div>
  );
};

/* ============================================================================
   EXAMPLE 3: RESPONSIVE BUTTON LAYOUT
   ============================================================================ */

export const ResponsiveButtonGroup = () => {
  return (
    <div className="
      /* Stack vertically on mobile, horizontally on desktop */
      flex flex-col sm:flex-row
      gap-3 sm:gap-4
      
      /* Center on mobile, align left on desktop */
      items-center sm:items-start
      justify-center sm:justify-start
    ">
      <button className="
        /* Full width on mobile, auto on desktop */
        w-full sm:w-auto
        
        /* Touch-friendly minimum height */
        px-4 py-3 sm:px-6 sm:py-2
        min-h-[48px] sm:min-h-auto
        
        /* Text sizing */
        text-base sm:text-sm
        font-medium
        
        /* Responsive styling */
        bg-blue-600 hover:bg-blue-700
        text-white
        rounded-lg
        transition-colors duration-200
        
        /* Focus state */
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
      ">
        Primary Action
      </button>
      
      <button className="
        w-full sm:w-auto
        px-4 py-3 sm:px-6 sm:py-2
        min-h-[48px] sm:min-h-auto
        text-base sm:text-sm
        font-medium
        bg-gray-200 hover:bg-gray-300
        text-gray-900
        rounded-lg
        transition-colors duration-200
      ">
        Secondary Action
      </button>
    </div>
  );
};

/* ============================================================================
   EXAMPLE 4: RESPONSIVE FORM
   ============================================================================ */

export const ResponsiveForm = () => {
  return (
    <form className="
      /* Container */
      w-full max-w-lg mx-auto
      px-4 sm:px-6 md:px-0
      py-6 sm:py-8
      
      /* Form spacing */
      space-y-4 sm:space-y-5 md:space-y-6
    ">
      <div className="space-y-2">
        <label className="
          block
          text-sm sm:text-base
          font-medium
          text-gray-700 dark:text-gray-300
          mb-2
        ">
          Email Address
        </label>
        <input
          type="email"
          className="
            /* Full width responsive */
            w-full
            
            /* Responsive padding */
            px-3 py-2 sm:px-4 sm:py-2.5
            
            /* Touch-friendly minimum height */
            min-h-[44px] sm:min-h-[40px]
            
            /* Text size - base on mobile to prevent zoom on iOS */
            text-base sm:text-sm
            
            /* Styling */
            border border-gray-300 dark:border-gray-600
            rounded-lg
            bg-white dark:bg-gray-800
            text-gray-900 dark:text-white
            placeholder-gray-500 dark:placeholder-gray-400
            
            /* Focus state */
            focus:outline-none focus:ring-2 focus:ring-blue-500
            focus:border-transparent
            
            /* Transition */
            transition-ring duration-200
          "
          placeholder="Enter your email"
        />
      </div>

      <button className="
        w-full
        px-4 py-3 sm:px-6 sm:py-2.5
        min-h-[48px] sm:min-h-auto
        text-base sm:text-sm font-medium
        bg-blue-600 hover:bg-blue-700
        text-white
        rounded-lg
        transition-colors duration-200
      ">
        Submit
      </button>
    </form>
  );
};

/* ============================================================================
   EXAMPLE 5: RESPONSIVE MODAL/DIALOG
   ============================================================================ */

export const ResponsiveModal = ({ isOpen, onClose }: any) => {
  return (
    isOpen && (
      <div className="
        /* Fixed overlay */
        fixed inset-0 bg-black bg-opacity-50
        z-50
        
        /* Flex centering */
        flex items-end sm:items-center justify-center
        
        /* Mobile padding */
        p-4 sm:p-6
      ">
        <div className="
          /* Modal sizing */
          w-full sm:w-auto sm:max-w-md md:max-w-lg
          
          /* Mobile-specific sizing */
          h-[90vh] sm:h-auto sm:max-h-[90vh]
          
          /* Mobile rounded corners - top only on mobile */
          rounded-t-2xl sm:rounded-lg
          
          /* Background */
          bg-white dark:bg-gray-900
          shadow-2xl
          
          /* Overflow */
          overflow-y-auto
        ">
          {/* Modal content with responsive padding */}
          <div className="p-4 sm:p-6 md:p-8 space-y-4 sm:space-y-5">
            <h2 className="
              text-xl sm:text-2xl font-bold
              text-gray-900 dark:text-white
            ">
              Modal Title
            </h2>
            
            <p className="
              text-sm sm:text-base
              text-gray-600 dark:text-gray-400
            ">
              Modal content goes here with responsive padding and text sizing.
            </p>
            
            <button
              onClick={onClose}
              className="
                w-full
                px-4 py-3 sm:px-6 sm:py-2
                min-h-[48px] sm:min-h-auto
                text-base sm:text-sm font-medium
                bg-blue-600 hover:bg-blue-700
                text-white rounded-lg
              "
            >
              Close
            </button>
          </div>
        </div>
      </div>
    )
  );
};

/* ============================================================================
   TOUCH-FRIENDLY BEST PRACTICES
   ============================================================================ */

export const TouchFriendlyComponent = () => {
  return (
    <div className="space-y-6">
      {/* Best Practice #1: Minimum tap target size of 48x48px */}
      <button className="min-h-[48px] min-w-[48px] px-4 py-3">
        Easy to tap on mobile
      </button>

      {/* Best Practice #2: Text input with base font size (prevents zoom on iOS) */}
      <input
        type="text"
        className="
          w-full px-4 py-3
          min-h-[48px]
          text-base sm:text-sm
          border rounded-lg
        "
      />

      {/* Best Practice #3: Adequate spacing between interactive elements */}
      <div className="space-y-4 sm:space-y-3">
        <button>Button 1</button>
        <button>Button 2</button>
      </div>

      {/* Best Practice #4: Readable font sizes */}
      <p className="text-base sm:text-sm leading-relaxed">
        Use text-base (16px) minimum on mobile for better readability
      </p>

      {/* Best Practice #5: Responsive images */}
      <img
        src="image.jpg"
        alt="Responsive"
        className="w-full h-auto object-cover object-center rounded-lg"
      />
    </div>
  );
};

/* ============================================================================
   TESTING CHECKLIST FOR MOBILE RESPONSIVENESS
   ============================================================================ */

/*
 * Use this checklist to verify mobile responsiveness:
 * 
 * [ ] Device Testing
 *     [ ] iPhone SE (375px width)
 *     [ ] iPhone 12 (390px width)
 *     [ ] iPhone 12 Pro Max (430px width)
 *     [ ] Android Phone (varies, test at 360px, 380px)
 *     [ ] Tablet (768px width)
 *     [ ] Desktop (1024px width)
 * 
 * [ ] Browser DevTools Testing
 *     [ ] Chrome DevTools responsive mode
 *     [ ] Firefox Responsive Design Mode
 *     [ ] Safari Responsive Design Mode
 * 
 * [ ] Touch Interactions
 *     [ ] All buttons are minimum 48x48px
 *     [ ] Buttons have adequate spacing (at least 8px between)
 *     [ ] Form inputs are easily tappable
 *     [ ] No hover-only information
 * 
 * [ ] Text Readability
 *     [ ] Font sizes are appropriate for each screen size
 *     [ ] Line heights are adequate (1.5+ recommended)
 *     [ ] Line lengths aren't too long on desktop
 *     [ ] Text contrast meets WCAG AA standards
 * 
 * [ ] Layout
 *     [ ] No horizontal scrolling on mobile
 *     [ ] Content is properly aligned
 *     [ ] Images scale correctly
 *     [ ] Padding and margins are appropriate
 * 
 * [ ] Orientation
 *     [ ] Portrait layout works well
 *     [ ] Landscape layout works (if applicable)
 *     [ ] Transitions between orientations are smooth
 * 
 * [ ] Performance
 *     [ ] Page loads quickly on mobile
 *     [ ] Images are optimized
 *     [ ] No unnecessary animations
 *     [ ] Responsive breakpoint changes don't cause layout shifts
 * 
 * [ ] Accessibility
 *     [ ] Touch targets are focused with keyboard navigation
 *     [ ] Focus outlines are visible
 *     [ ] Color contrast is sufficient
 *     [ ] Text is readable without zooming
 */

export default ResponsiveCard;
