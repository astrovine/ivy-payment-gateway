import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useEffect, useState } from 'react'
import { Globe, ShieldCheck, Zap, Check } from 'lucide-react'

import revolutIcon from '../assets/icons8-revolut-50.png'
import boaIcon from '../assets/icons8-bank-of-america-50.png'
import airbnbIcon from '../assets/icons8-airbnb-50.png'
import britishAirwaysIcon from '../assets/icons8-british-airways-50.png'
import vectionIcon from '../assets/icons8-vection-group-50.png'

export default function LandingPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [currentValue, setCurrentValue] = useState(0)
  const [hideNav, setHideNav] = useState(false)

  const values = [
    "built for scale",
    "trusted by thousands",
    "secure & compliant",
    "lightning fast"
  ]

  useEffect(() => {
    if (token) {
      navigate('/dashboard')
    }
  }, [token, navigate])

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)

      const businessSection = document.getElementById('business-types')
      const footer = document.getElementById('support')

      if (businessSection && footer) {
        const businessTop = businessSection.offsetTop
        const footerTop = footer.offsetTop
        const scrollPosition = window.scrollY + window.innerHeight / 3

        if (scrollPosition >= businessTop && scrollPosition < footerTop) {
          setHideNav(true)
        } else {
          setHideNav(false)
        }
      }
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentValue((prev) => (prev + 1) % values.length)
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-fade-in-up')
          }
        })
      },
      { threshold: 0.1, rootMargin: '50px' }
    )

    document.querySelectorAll('.scroll-animate').forEach((el) => {
      observer.observe(el)
    })

    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    const cards = document.querySelectorAll('.use-case-card')
    if (!cards.length) return

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            entry.target.style.opacity = '1'
            entry.target.style.transform = 'translateY(0)'
          }, index * 100)
        }
      })
    }, { threshold: 0.2 })

    cards.forEach(card => {
      card.style.opacity = '0'
      card.style.transform = 'translateY(40px)'
      card.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)'
      observer.observe(card)
    })

    return () => observer.disconnect()
  }, [])

  if (token) {
    return null
  }

  const trustedCompanies = [

    { name: 'Revolut', logo: revolutIcon },

    { name: 'Bank of America', logo: boaIcon },
    { name: 'Airbnb', logo: airbnbIcon },
    { name: 'British Airways', logo: britishAirwaysIcon },
    { name: 'Vection Group', logo: vectionIcon }
  ]

  return (
    <div className="min-h-screen bg-white grain font-sans antialiased">
      


        <nav className={`fixed top-0 w-full z-50 transition-all duration-500 ${
          hideNav ? '-translate-y-full opacity-0' : 'translate-y-0 opacity-100'
        } ${
          scrolled ? 'bg-white/95 backdrop-blur-xl border-b border-neutral-200 shadow-sm' : 'bg-white/98 backdrop-blur-md'
        }`}>
        <div className="max-w-7xl mx-auto px-4 md:px-6 py-3 md:py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6 md:gap-12">
              <Link to="/" className="flex items-center gap-2 md:gap-3">
                <div className="w-8 h-8 md:w-9 md:h-9 bg-neutral-900 rounded-xl flex items-center justify-center shadow-sm">
                  <svg className="w-4 h-4 md:w-5 md:h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707" />
                  </svg>
                </div>
                <span className="text-xl md:text-2xl font-semibold tracking-tight">Ivy</span>
              </Link>


              <div className="hidden lg:flex items-center gap-8">
                <a href="#products" className="text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors">
                  Products
                </a>
                <a href="#developers" className="text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors">
                  Developers
                </a>
                <a href="#docs" className="text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors">
                  Docs
                </a>
                <a href="#pricing" className="text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors">
                  Pricing
                </a>
                <a href="#api" className="text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors">
                  API
                </a>
                <a href="#support" className="text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors">
                  Support
                </a>
              </div>
            </div>

            <div className="flex items-center gap-2 md:gap-3">
              <Link to="/login" className="btn-ghost text-sm md:text-base px-4 md:px-6 py-2 md:py-2.5 font-medium">
                Sign in
              </Link>
              <Link to="/register" className="btn-primary text-sm md:text-base px-5 md:px-7 py-2 md:py-2.5 font-medium shadow-lg shadow-neutral-900/10 hover:shadow-xl">
                Get started
              </Link>
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 hover:bg-neutral-100 rounded-lg transition-colors ml-2"
                aria-label="Toggle menu"
              >
                <svg className="w-6 h-6 text-neutral-900" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  {mobileMenuOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            </div>
          </div>


          {mobileMenuOpen && (
            <div className="lg:hidden border-t border-neutral-200 mt-3 animate-slide-up">
              <div className="px-4 py-3 space-y-1">
                <a href="#products" onClick={() => setMobileMenuOpen(false)} className="block text-base font-medium text-neutral-700 hover:text-neutral-900 hover:bg-neutral-50 py-3 px-4 rounded-lg transition-colors">
                  Products
                </a>
                <a href="#developers" onClick={() => setMobileMenuOpen(false)} className="block text-base font-medium text-neutral-700 hover:text-neutral-900 hover:bg-neutral-50 py-3 px-4 rounded-lg transition-colors">
                  Developers
                </a>
                <a href="#docs" onClick={() => setMobileMenuOpen(false)} className="block text-base font-medium text-neutral-700 hover:text-neutral-900 hover:bg-neutral-50 py-3 px-4 rounded-lg transition-colors">
                  Docs
                </a>
                <a href="#pricing" onClick={() => setMobileMenuOpen(false)} className="block text-base font-medium text-neutral-700 hover:text-neutral-900 hover:bg-neutral-50 py-3 px-4 rounded-lg transition-colors">
                  Pricing
                </a>
                <a href="#api" onClick={() => setMobileMenuOpen(false)} className="block text-base font-medium text-neutral-700 hover:text-neutral-900 hover:bg-neutral-50 py-3 px-4 rounded-lg transition-colors">
                  API
                </a>
                <a href="#support" onClick={() => setMobileMenuOpen(false)} className="block text-base font-medium text-neutral-700 hover:text-neutral-900 hover:bg-neutral-50 py-3 px-4 rounded-lg transition-colors">
                  Support
                </a>
              </div>
            </div>
          )}
        </div>
      </nav>


      <section className="pt-20 md:pt-40 pb-16 md:pb-24 px-4 md:px-6 relative overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(0,0,0,0.05),transparent)]" />
        </div>

        <div className="max-w-7xl mx-auto">
          <div className="text-center space-y-8 md:space-y-11">

            <div className="animate-in">
              <div className="inline-flex items-center gap-2.5 px-5 py-2.5 bg-white/80 backdrop-blur-sm rounded-full text-sm font-semibold text-neutral-700 mb-10 md:mb-12 border border-neutral-200 shadow-sm">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                </span>
                <span className="hidden sm:inline tabular-nums lining-nums">Trusted by 12,500+ businesses worldwide</span>
                <span className="sm:hidden tabular-nums lining-nums">12,500+ businesses</span>
              </div>
            </div>


            <div className="relative">
              <h1 className="relative z-10 animate-in-1 px-4 hero-headline max-w-6xl mx-auto">

                <span className="block text-[2.75rem] sm:text-[3.5rem] md:text-[4.5rem] lg:text-[5.5rem] xl:text-[6.5rem] font-extrabold tracking-[-0.04em] leading-[1.08] mb-3 md:mb-4">
                  <span className="bg-gradient-to-br from-neutral-950 via-neutral-800 to-neutral-900 bg-clip-text text-transparent">
                    Financial infrastructure
                  </span>
                </span>

                <span className="block text-[2.25rem] sm:text-[3rem] md:text-[4rem] lg:text-[5rem] xl:text-[5.75rem] font-bold tracking-[-0.03em] leading-[1.15] relative h-[2.5rem] sm:h-[3.5rem] md:h-[4.5rem] lg:h-[5.5rem] xl:h-[6.25rem]">
                  {values.map((value, i) => (
                    <span
                      key={i}
                      className="absolute inset-0 transition-opacity duration-500 bg-gradient-to-br from-neutral-500 via-neutral-600 to-neutral-500 bg-clip-text text-transparent"
                      style={{ opacity: currentValue === i ? 1 : 0 }}
                    >
                      {value}
                    </span>
                  ))}
                </span>
              </h1>
            </div>


            <p className="text-lg sm:text-xl md:text-2xl text-neutral-600 max-w-4xl mx-auto leading-[1.6] px-6 font-normal tracking-[-0.012em]">
              Enterprise-grade payment platform for modern businesses. Accept payments globally, manage treasury operations, and scale with confidence.
            </p>


            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-6 md:pt-8 animate-in-3 px-4">
              <Link to="/register" className="group relative w-full sm:w-auto text-base md:text-lg px-10 md:px-12 py-4 md:py-4.5 bg-neutral-900 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] tracking-tight min-h-[48px]">
                <span className="relative z-10 flex items-center justify-center gap-2.5">
                  Start building now
                  <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </span>
              </Link>

              <a href="#demo" className="group text-neutral-700 hover:text-neutral-900 text-base md:text-lg font-medium inline-flex items-center justify-center gap-2.5 px-6 py-3 rounded-xl hover:bg-neutral-50 transition-all tracking-tight min-h-[48px] w-full sm:w-auto">
                <svg className="w-5 h-5 text-neutral-600 group-hover:text-neutral-900 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Watch demo</span>
              </a>
            </div>


            <div className="pt-16 md:pt-20 grid grid-cols-1 sm:grid-cols-3 gap-10 sm:gap-8 md:gap-12 max-w-4xl mx-auto animate-in-4 px-4">
              <div className="text-center">
                <div className="text-4xl sm:text-3xl md:text-5xl font-bold text-neutral-900 mb-2 tabular-nums lining-nums tracking-tight">₦4.2B+</div>
                <div className="text-sm md:text-sm text-neutral-600 font-medium">Processed annually</div>
              </div>
              <div className="text-center">
                <div className="text-4xl sm:text-3xl md:text-5xl font-bold text-neutral-900 mb-2 tabular-nums lining-nums tracking-tight">150+</div>
                <div className="text-sm md:text-sm text-neutral-600 font-medium">Countries</div>
              </div>
              <div className="text-center">
                <div className="text-4xl sm:text-3xl md:text-5xl font-bold text-neutral-900 mb-2 tabular-nums lining-nums tracking-tight">99.99%</div>
                <div className="text-sm md:text-sm text-neutral-600 font-medium">Uptime SLA</div>
              </div>
            </div>
          </div>


          <div className="hidden lg:block mt-16 md:mt-24 animate-in-5 px-4">
            <div className="relative">
              <div className="absolute -inset-4 md:-inset-8 bg-gradient-to-r from-neutral-100 via-neutral-50 to-neutral-100 rounded-2xl md:rounded-3xl blur-3xl opacity-40" />
              <div className="relative">
                <div className="card shadow-2xl border-neutral-300 overflow-hidden">

                  <div className="bg-neutral-900 px-3 md:px-4 py-3 md:py-4 flex items-center justify-between border-b border-neutral-800">
                    <div className="flex items-center gap-2 md:gap-3">
                      <div className="flex gap-1 md:gap-1.5">
                        <div className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-red-500" />
                        <div className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-yellow-500" />
                        <div className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-emerald-500" />
                      </div>
                      <span className="text-white text-xs md:text-sm font-medium">Dashboard Preview</span>
                    </div>
                  </div>


                  <div className="bg-neutral-50 p-6 md:p-8 space-y-4 md:space-y-6">

                    <div className="flex items-center justify-between flex-wrap gap-4">
                      <div>
                        <h2 className="text-lg md:text-2xl font-bold tracking-tight text-neutral-900 mb-1">Welcome back, Divine!</h2>
                        <p className="text-neutral-600 text-xs md:text-sm">Here's what's happening today</p>
                      </div>
                      <button className="px-4 py-2 bg-neutral-900 text-white text-xs md:text-sm font-medium rounded-lg">
                        Create Charge
                      </button>
                    </div>


                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-5">

                      <div className="bg-white rounded-xl p-4 md:p-6 border border-neutral-200 shadow-sm">
                        <div className="flex items-center justify-between mb-2 md:mb-3">
                          <span className="text-xs font-medium text-neutral-500 uppercase">Available</span>
                          <div className="w-6 h-6 md:w-8 md:h-8 rounded-lg bg-emerald-50 flex items-center justify-center">
                            <svg className="w-3 h-3 md:w-4 md:h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </div>
                        </div>
                        <div className="text-3xl font-bold text-neutral-900 mb-1 tabular-nums lining-nums">₦84,580.50</div>
                        <div className="text-xs md:text-sm">
                          <span className="text-emerald-600 font-semibold">↑ 12.5%</span>
                        </div>
                      </div>


                      <div className="bg-white rounded-xl p-6 border border-neutral-200 shadow-sm hover:shadow-md transition-all">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-xs font-medium text-neutral-500 uppercase tracking-wide">Pending</span>
                          <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center">
                            <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </div>
                        </div>
                        <div className="text-3xl font-bold text-neutral-900 mb-1 tabular-nums lining-nums">₦90,240.00</div>
                        <div className="flex items-center gap-1 text-sm">
                          <span className="text-amber-600 font-semibold">18 transactions</span>
                          <span className="text-neutral-500">processing</span>
                        </div>
                      </div>


                      <div className="bg-white rounded-xl p-6 border border-neutral-200 shadow-sm hover:shadow-md transition-all">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-xs font-medium text-neutral-500 uppercase tracking-wide">Total Volume</span>
                          <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
                            <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                            </svg>
                          </div>
                        </div>
                        <div className="text-3xl font-bold text-neutral-900 mb-1 tabular-nums lining-nums">₦174,820.00</div>
                        <div className="flex items-center gap-1 text-sm">
                          <span className="text-blue-600 font-semibold">↑ 8.2%</span>
                          <span className="text-neutral-500">this month</span>
                        </div>
                      </div>
                    </div>


                    <div className="bg-white rounded-xl border border-neutral-200 overflow-hidden">
                      <div className="px-6 py-4 border-b border-neutral-200 flex items-center justify-between">
                        <h3 className="font-semibold tracking-tight text-neutral-900">Recent Transactions</h3>
                        <button className="text-sm text-neutral-600 hover:text-neutral-900 font-medium">View all →</button>
                      </div>
                      <div className="divide-y divide-neutral-100">
                        {[
                          { id: 'ch_abc123', amount: '₦20,400.00', customer: 'Acme Corp', status: 'succeeded', time: '2 min ago' },
                          { id: 'ch_def456', amount: '₦67,200.00', customer: 'TechStart Inc', status: 'pending', time: '15 min ago' },
                          { id: 'ch_ghi789', amount: '₦18,550.00', customer: 'Design Studio', status: 'succeeded', time: '1 hour ago' },
                          { id: 'ch_jkl012', amount: '₦52,600.00', customer: 'Global Ltd', status: 'succeeded', time: '2 hours ago' }
                        ].map((tx, i) => (
                          <div key={i} className="px-6 py-4 flex items-center justify-between hover:bg-neutral-50 transition-colors">
                            <div className="flex items-center gap-4 flex-1">
                              <div className={`w-2 h-2 rounded-full ${
                                tx.status === 'succeeded' ? 'bg-emerald-500' : 'bg-amber-500'
                              }`} />
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-3">
                                  <span className="font-mono text-sm font-medium text-neutral-900">{tx.id}</span>
                                  <span className="text-sm text-neutral-600">{tx.customer}</span>
                                </div>
                                <div className="text-xs text-neutral-500 mt-0.5">{tx.time}</div>
                              </div>
                            </div>
                            <div className="flex items-center gap-4">
                              <span className="font-semibold text-neutral-900 tabular-nums lining-nums">{tx.amount}</span>
                              <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                                tx.status === 'succeeded'
                                  ? 'bg-emerald-50 text-emerald-700'
                                  : 'bg-amber-50 text-amber-700'
                              }`}>
                                {tx.status}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>



      <section className="py-20 md:py-24 px-6 bg-neutral-50/50 border-y border-neutral-200 overflow-hidden">
        <div className="max-w-full mx-auto">
          <p className="text-center text-xs font-semibold text-neutral-500 tracking-wider uppercase mb-10 md:mb-14">
            Powering payments for industry leaders
          </p>

          <div className="relative">
            <div className="logos-scroll-container group">
              <div className="logos-scroll flex items-center gap-12 md:gap-16 lg:gap-20">

                {[...trustedCompanies, ...trustedCompanies].map((company, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col items-center justify-center opacity-60 hover:opacity-100 transition-opacity duration-300 flex-shrink-0"
                  >
                    <div className="w-20 h-20 md:w-24 md:h-24 bg-white rounded-2xl border-2 border-neutral-200 flex items-center justify-center p-4 md:p-5 hover:border-neutral-300 hover:shadow-xl transition-all duration-300 transform hover:scale-105">
                      <img
                        src={company.logo}
                        alt={company.name}
                        className="w-full h-full object-contain grayscale hover:grayscale-0 transition-all duration-300"
                      />
                    </div>
                    <span className="text-xs md:text-sm font-semibold text-neutral-600 mt-3 whitespace-nowrap">
                      {company.name}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>


      <section id="products" className="py-32 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
            <div>
              <div className="inline-block px-3 py-1 bg-neutral-900 text-white text-xs font-bold uppercase tracking-widest rounded-md mb-8">
                Infrastructure
              </div>
              <h2 className="text-5xl md:text-6xl font-bold text-neutral-900 mb-6 tracking-tight leading-tight">
                Built for the<br/>modern economy
              </h2>
              <p className="text-xl text-neutral-600 leading-relaxed">
                Enterprise-grade payment infrastructure trusted by thousands of businesses worldwide.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:gap-4 md:gap-6">
              <div className="space-y-3 sm:space-y-4 md:space-y-6">
                <div className="bg-neutral-900 text-white p-4 sm:p-6 md:p-8 rounded-xl md:rounded-2xl">
                  <div className="text-3xl sm:text-4xl md:text-5xl font-bold mb-1 sm:mb-2 tabular-nums">135+</div>
                  <div className="text-xs sm:text-sm text-neutral-400">Currencies</div>
                </div>
                <div className="bg-white border-2 border-neutral-200 p-4 sm:p-6 md:p-8 rounded-xl md:rounded-2xl">
                  <div className="text-3xl sm:text-4xl md:text-5xl font-bold mb-1 sm:mb-2 text-neutral-900 tabular-nums">150+</div>
                  <div className="text-xs sm:text-sm text-neutral-600">Countries</div>
                </div>
              </div>
              <div className="space-y-3 sm:space-y-4 md:space-y-6 pt-6 sm:pt-8 md:pt-12">
                <div className="bg-white border-2 border-neutral-200 p-4 sm:p-6 md:p-8 rounded-xl md:rounded-2xl">
                  <div className="text-3xl sm:text-4xl md:text-5xl font-bold mb-1 sm:mb-2 text-neutral-900 tabular-nums">99.99%</div>
                  <div className="text-xs sm:text-sm text-neutral-600">Uptime</div>
                </div>
                <div className="bg-neutral-900 text-white p-4 sm:p-6 md:p-8 rounded-xl md:rounded-2xl">
                  <div className="text-3xl sm:text-4xl md:text-5xl font-bold mb-1 sm:mb-2 tabular-nums break-all">&lt;500ms</div>
                  <div className="text-xs sm:text-sm text-neutral-400">Response</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>


      <section id="business-types" className="py-32 px-6 bg-neutral-900 relative overflow-hidden">

        <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-transparent via-neutral-700 to-transparent hidden lg:block" />

        <div className="max-w-7xl mx-auto">

          <div className="text-center mb-32 relative z-10">
            <h2 className="text-5xl md:text-6xl font-bold text-white mb-6 tracking-tight">
              Powering businesses worldwide
            </h2>
            <p className="text-xl text-neutral-400 max-w-3xl mx-auto leading-relaxed">
              From startups to enterprises, Ivy's infrastructure adapts to your unique needs. See how we empower different industries.
            </p>
          </div>


          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center mb-40 relative scroll-animate opacity-0">

            <div className="order-2 lg:order-1 space-y-6">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-full mb-4">
                <div className="w-2 h-2 rounded-full bg-white animate-pulse"></div>
                <span className="text-sm font-semibold text-neutral-300 uppercase tracking-wider">E-Commerce</span>
              </div>
              <h3 className="text-4xl md:text-5xl font-bold text-white leading-tight">
                High-volume retail that scales
              </h3>
              <p className="text-lg text-neutral-400 leading-relaxed">
                Handle peak season traffic with auto-scaling infrastructure. Process 10K+ transactions per minute with sub-500ms response times. Your customers get a seamless checkout experience, every time.
              </p>
              <div className="space-y-4 pt-4">
                <div className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 mt-1">
                    <Check className="w-4 h-4 text-white" strokeWidth={2.5} />
                  </div>
                  <div>
                    <p className="font-semibold text-white">Multi-currency checkout</p>
                    <p className="text-sm text-neutral-400">Accept payments in 135+ currencies with automatic conversion</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 mt-1">
                    <Check className="w-4 h-4 text-white" strokeWidth={2.5} />
                  </div>
                  <div>
                    <p className="font-semibold text-white">AI fraud detection</p>
                    <p className="text-sm text-neutral-400">0.02% false positive rate with machine learning protection</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 mt-1">
                    <Check className="w-4 h-4 text-white" strokeWidth={2.5} />
                  </div>
                  <div>
                    <p className="font-semibold text-white">Cart recovery automation</p>
                    <p className="text-sm text-neutral-400">Recover up to 30% of abandoned carts automatically</p>
                  </div>
                </div>
              </div>
            </div>


            <div className="order-1 lg:order-2 relative">
              <div className="relative mx-auto w-[320px] h-[640px]">

                <div className="absolute inset-0 bg-neutral-800 rounded-[3rem] border-8 border-neutral-900 shadow-2xl overflow-hidden">

                  <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-7 bg-neutral-900 rounded-b-3xl z-10" />


                  <div className="absolute inset-0 bg-white p-6 pt-12 overflow-hidden">
                    <div className="animate-fade-in-up space-y-6">

                      <div className="flex items-center justify-between">
                        <h4 className="text-xl font-bold text-neutral-900">Checkout</h4>
                        <span className="text-sm text-emerald-600 font-semibold">Secure</span>
                      </div>


                      <div className="bg-neutral-50 rounded-2xl p-4 space-y-3">
                        <div className="flex justify-between text-sm">
                          <span className="text-neutral-600">Premium Plan (Annual)</span>
                          <span className="font-semibold text-neutral-900">₦1,598,400</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-neutral-600">Tax</span>
                          <span className="font-semibold text-neutral-900">₦159,840</span>
                        </div>
                        <div className="border-t border-neutral-200 pt-3 flex justify-between">
                          <span className="font-bold text-neutral-900">Total</span>
                          <span className="font-bold text-neutral-900 text-lg">₦1,758,240</span>
                        </div>
                      </div>


                      <div className="space-y-3 animate-slide-up" style={{animationDelay: '0.3s'}}>
                        <label className="text-sm font-semibold text-neutral-900">Payment Method</label>
                        <div className="bg-gradient-to-r from-neutral-800 to-neutral-900 rounded-xl p-4 text-white shadow-lg">
                          <div className="flex justify-between items-start mb-8">
                            <svg className="w-10 h-10" fill="currentColor" viewBox="0 0 24 24">
                              <rect x="2" y="4" width="20" height="16" rx="3" fill="white" fillOpacity="0.2"/>
                              <rect x="2" y="8" width="20" height="3" fill="white" fillOpacity="0.4"/>
                            </svg>
                            <span className="text-xs font-semibold">VISA</span>
                          </div>
                          <div className="font-mono text-base tracking-wider mb-3">•••• •••• •••• 4242</div>
                          <div className="flex justify-between text-xs">
                            <span>Frank Ocean</span>
                            <span>12/25</span>
                          </div>
                        </div>
                      </div>


                      <button className="w-full bg-neutral-900 text-white font-semibold py-4 rounded-xl animate-pulse-subtle" style={{animationDelay: '0.6s'}}>
                        Pay ₦1,758,240
                      </button>


                      <div className="flex items-center justify-center gap-2 text-xs text-neutral-500">
                        <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                        <span>Secured by Ivy</span>
                      </div>
                    </div>
                  </div>
                </div>


                <div className="absolute -inset-4 bg-white/10 rounded-[4rem] blur-3xl -z-10 animate-pulse-slow" />
              </div>
            </div>
          </div>


          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center mb-40 relative scroll-animate opacity-0">

            <div className="relative">
              <div className="relative mx-auto w-[320px] h-[640px]">

                <div className="absolute inset-0 bg-neutral-800 rounded-[3rem] border-8 border-neutral-900 shadow-2xl overflow-hidden">
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-7 bg-neutral-900 rounded-b-3xl z-10" />


                  <div className="absolute inset-0 bg-gradient-to-br from-neutral-50 to-white p-6 pt-12 overflow-hidden">
                    <div className="animate-fade-in-up space-y-5">

                      <div>
                        <h4 className="text-2xl font-bold text-neutral-900 mb-1">Subscriptions</h4>
                        <p className="text-sm text-neutral-600">Manage recurring billing</p>
                      </div>


                      <div className="bg-gradient-to-br from-neutral-800 to-neutral-900 rounded-2xl p-5 text-white shadow-lg">
                        <div className="text-sm font-medium mb-2 opacity-90">Monthly Recurring Revenue</div>
                        <div className="text-4xl font-bold mb-3 tabular-nums">₦685,600</div>
                        <div className="flex items-center gap-2 text-sm">
                          <span className="px-2 py-1 bg-white/20 rounded-full font-semibold">↑ 18.5%</span>
                          <span className="opacity-90">vs last month</span>
                        </div>
                      </div>


                      <div className="bg-white rounded-2xl p-4 border border-neutral-200 shadow-sm space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-semibold text-neutral-900">Active Subscriptions</span>
                          <span className="text-2xl font-bold text-neutral-900 tabular-nums">1,247</span>
                        </div>


                        <div className="flex items-end gap-1 h-16">
                          {[40, 65, 45, 80, 60, 90, 100].map((height, i) => (
                            <div key={i} className="flex-1 bg-gradient-to-t from-neutral-800 to-neutral-600 rounded-t animate-grow-up" style={{height: `${height}%`, animationDelay: `${i * 0.1}s`}} />
                          ))}
                        </div>
                      </div>


                      <div className="space-y-2">
                        <h5 className="text-xs font-semibold text-neutral-500 uppercase tracking-wide">Recent Activity</h5>
                        {[
                          { name: 'Pro Plan', amount: '+₦80,000', status: 'success' },
                          { name: 'Enterprise', amount: '₦20,000', status: 'success' },
                          { name: 'Starter', amount: '+₦34,000', status: 'pending' }
                        ].map((item, i) => (
                          <div key={i} className="flex items-center justify-between bg-white rounded-xl p-3 border border-neutral-200 animate-slide-right" style={{animationDelay: `${i * 0.15 + 0.5}s`}}>
                            <div className="flex items-center gap-3">
                              <div className={`w-2 h-2 rounded-full ${item.status === 'success' ? 'bg-neutral-900' : 'bg-neutral-400'}`} />
                              <span className="text-sm font-medium text-neutral-900">{item.name}</span>
                            </div>
                            <span className="text-sm font-bold text-neutral-900 tabular-nums">{item.amount}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="absolute -inset-4 bg-white/10 rounded-[4rem] blur-3xl -z-10 animate-pulse-slow" />
              </div>
            </div>


            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-full mb-4">
                <div className="w-2 h-2 rounded-full bg-white animate-pulse"></div>
                <span className="text-sm font-semibold text-neutral-300 uppercase tracking-wider">SaaS</span>
              </div>
              <h3 className="text-4xl md:text-5xl font-bold text-white leading-tight">
                Subscription billing made simple
              </h3>
              <p className="text-lg text-neutral-400 leading-relaxed">
                Recurring revenue management that just works. Automated billing, prorated upgrades, usage-based pricing, and smart dunning that recovers 34% of failed payments. Focus on your product, we'll handle the billing.
              </p>
              <div className="space-y-4 pt-4">
                <div className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 mt-1">
                    <Check className="w-4 h-4 text-white" strokeWidth={2.5} />
                  </div>
                  <div>
                    <p className="font-semibold text-white">Automatic invoicing</p>
                    <p className="text-sm text-neutral-400">Generate and send invoices automatically with every billing cycle</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 mt-1">
                    <Check className="w-4 h-4 text-white" strokeWidth={2.5} />
                  </div>
                  <div>
                    <p className="font-semibold text-white">Metered billing</p>
                    <p className="text-sm text-neutral-400">Charge based on actual usage with flexible pricing tiers</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 mt-1">
                    <Check className="w-4 h-4 text-white" strokeWidth={2.5} />
                  </div>
                  <div>
                    <p className="font-semibold text-white">Customer portal</p>
                    <p className="text-sm text-neutral-400">Self-service billing management for your customers</p>
                  </div>
                </div>
              </div>
            </div>
          </div>


          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center relative scroll-animate opacity-0">

            <div className="order-2 lg:order-1 space-y-6">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-full mb-4">
                <div className="w-2 h-2 rounded-full bg-white animate-pulse"></div>
                <span className="text-sm font-semibold text-neutral-300 uppercase tracking-wider">Marketplace</span>
              </div>
              <h3 className="text-4xl md:text-5xl font-bold text-white leading-tight">
                Multi-party payouts simplified
              </h3>
              <p className="text-lg text-neutral-400 leading-relaxed">
                Split payments between buyers, sellers, and your platform with atomic transactions. Handle escrow, commission management, and instant seller payouts effortlessly. Perfect for marketplaces, gig platforms, and multi-vendor stores.
              </p>
              <div className="space-y-4 pt-4">
                <div className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 mt-1">
                    <Check className="w-4 h-4 text-white" strokeWidth={2.5} />
                  </div>
                  <div>
                    <p className="font-semibold text-white">Instant payouts</p>
                    <p className="text-sm text-neutral-400">Pay sellers in real-time, 24/7, with no delays</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 mt-1">
                    <Check className="w-4 h-4 text-white" strokeWidth={2.5} />
                  </div>
                  <div>
                    <p className="font-semibold text-white">Flexible commissions</p>
                    <p className="text-sm text-neutral-400">Dynamic commission structures per seller or transaction</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 mt-1">
                    <Check className="w-4 h-4 text-white" strokeWidth={2.5} />
                  </div>
                  <div>
                    <p className="font-semibold text-white">Seller analytics</p>
                    <p className="text-sm text-neutral-400">Individual dashboards for each seller with detailed insights</p>
                  </div>
                </div>
              </div>
            </div>


            <div className="order-1 lg:order-2 relative">
              <div className="relative mx-auto w-[320px] h-[640px]">

                <div className="absolute inset-0 bg-neutral-800 rounded-[3rem] border-8 border-neutral-900 shadow-2xl overflow-hidden">
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-7 bg-neutral-900 rounded-b-3xl z-10" />


                  <div className="absolute inset-0 bg-gradient-to-br from-neutral-50 to-white p-6 pt-12 overflow-hidden">
                    <div className="animate-fade-in-up space-y-6">

                      <div>
                        <h4 className="text-2xl font-bold text-neutral-900 mb-1">Payment Split</h4>
                        <p className="text-sm text-neutral-600">Transaction #12849</p>
                      </div>


                      <div className="bg-gradient-to-br from-neutral-800 to-neutral-900 rounded-2xl p-6 text-white text-center shadow-lg">
                        <div className="text-sm font-medium mb-2 opacity-90">Total Amount</div>
                        <div className="text-5xl font-bold tabular-nums">₦451,000</div>
                      </div>


                      <div className="space-y-3">

                        <div className="flex justify-center">
                          <svg className="w-6 h-6 text-neutral-400 animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                          </svg>
                        </div>


                        <div className="bg-white rounded-xl p-4 border-2 border-neutral-300 shadow-sm animate-slide-right" style={{animationDelay: '0.3s'}}>
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-neutral-100 rounded-full flex items-center justify-center">
                                <span className="text-lg">👤</span>
                              </div>
                              <div>
                                <p className="font-semibold text-neutral-900">Seller</p>
                                <p className="text-xs text-neutral-600">85% commission</p>
                              </div>
                            </div>
                            <span className="text-xl font-bold text-neutral-900 tabular-nums">₦163,000</span>
                          </div>
                        </div>


                        <div className="bg-white rounded-xl p-4 border-2 border-neutral-300 shadow-sm animate-slide-right" style={{animationDelay: '0.5s'}}>
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-neutral-100 rounded-full flex items-center justify-center">
                                <span className="text-lg">🏢</span>
                              </div>
                              <div>
                                <p className="font-semibold text-neutral-900">Platform</p>
                                <p className="text-xs text-neutral-600">12% commission</p>
                              </div>
                            </div>
                            <span className="text-xl font-bold text-neutral-900 tabular-nums">₦230,400</span>
                          </div>
                        </div>


                        <div className="bg-white rounded-xl p-4 border-2 border-neutral-200 shadow-sm animate-slide-right" style={{animationDelay: '0.7s'}}>
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-neutral-100 rounded-full flex items-center justify-center">
                                <span className="text-lg">⚡</span>
                              </div>
                              <div>
                                <p className="font-semibold text-neutral-900">Processing</p>
                                <p className="text-xs text-neutral-600">3% fee</p>
                              </div>
                            </div>
                            <span className="text-xl font-bold text-neutral-600 tabular-nums">₦57,600</span>
                          </div>
                        </div>
                      </div>


                      <div className="flex items-center justify-center gap-2 pt-4">
                        <div className="w-2 h-2 rounded-full bg-neutral-900 animate-pulse"></div>
                        <span className="text-sm font-semibold text-neutral-900">Completed instantly</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="absolute -inset-4 bg-white/10 rounded-[4rem] blur-3xl -z-10 animate-pulse-slow" />
              </div>
            </div>
          </div>
        </div>
      </section>


      <section id="api" className="py-32 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">

            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-100 rounded-full text-sm font-medium text-neutral-700 mb-6 border border-neutral-200">
                <svg className="w-4 h-4 text-neutral-900" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                <span>Developer-first platform</span>
              </div>
              <h2 className="text-5xl font-bold tracking-tight mb-6">
                Build with powerful APIs
              </h2>
              <p className="text-xl text-neutral-600 mb-10 leading-relaxed">
                Integrate Ivy's payment infrastructure with our developer-friendly APIs.
                Production-ready in minutes, not weeks. Built for developers who demand flexibility and reliability.
              </p>


              <div className="space-y-5 mb-10">
                {[
                  {
                    title: 'RESTful API design',
                    description: 'Intuitive endpoints with comprehensive documentation and examples'
                  },
                  {
                    title: 'Real-time webhooks',
                    description: 'Instant notifications for all payment events and state changes'
                  },
                  {
                    title: 'Test mode included',
                    description: 'Sandbox environment with test cards and data for development'
                  },
                  {
                    title: 'Official SDKs',
                    description: 'Libraries for Python, Node.js, Ruby, PHP, Go, and .NET'
                  }
                ].map((item, idx) => (
                  <div key={idx} className="flex items-start gap-4">
                    <div className="w-5 h-5 rounded flex items-center justify-center flex-shrink-0 mt-0.5 border-2 border-neutral-900">
                      <svg className="w-3 h-3 text-neutral-900" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-semibold text-neutral-900 mb-1">{item.title}</p>
                      <p className="text-sm text-neutral-600 leading-relaxed">{item.description}</p>
                    </div>
                  </div>
                ))}
              </div>


              <div className="flex flex-wrap gap-4">
                <Link
                  to="/register"
                  className="btn-primary text-base px-8 py-3.5 inline-flex items-center gap-2 font-medium shadow-lg hover:shadow-xl"
                >
                  Get API keys
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </Link>
                <a
                  href="#docs"
                  className="btn-secondary text-base px-8 py-3.5 inline-flex items-center gap-2 font-medium"
                >
                  View documentation
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </a>
              </div>


              <div className="mt-12 pt-10 border-t border-neutral-200">
                <p className="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-6">Official SDKs & Libraries</p>
                <div className="grid grid-cols-3 gap-6">
                  {[
                    {
                      name: 'Python',
                      icon: (
                        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none">
                          <path d="M14.31.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.83l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.23l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.24l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33.22-.41.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24.4.16.36.09.32.05.24.02.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35.14.33.1.3.06.26.04.21.02.13.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01.21.03zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z" fill="currentColor"/>
                        </svg>
                      )
                    },
                    {
                      name: 'Node.js',
                      icon: (
                        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none">
                          <path d="M11.998,24c-0.321,0-0.641-0.084-0.922-0.247l-2.936-1.737c-0.438-0.245-0.224-0.332-0.08-0.383 c0.585-0.203,0.703-0.25,1.328-0.604c0.065-0.037,0.151-0.023,0.218,0.017l2.256,1.339c0.082,0.045,0.197,0.045,0.272,0l8.795-5.076 c0.082-0.047,0.134-0.141,0.134-0.238V6.921c0-0.099-0.053-0.192-0.137-0.242l-8.791-5.072c-0.081-0.047-0.189-0.047-0.271,0 L3.075,6.68C2.99,6.729,2.936,6.825,2.936,6.921v10.15c0,0.097,0.054,0.189,0.139,0.235l2.409,1.392 c1.307,0.654,2.108-0.116,2.108-0.89V7.787c0-0.142,0.114-0.253,0.256-0.253h1.115c0.139,0,0.255,0.112,0.255,0.253v10.021 c0,1.745-0.95,2.745-2.604,2.745c-0.508,0-0.909,0-2.026-0.551L2.28,18.675c-0.57-0.329-0.922-0.945-0.922-1.604V6.921 c0-0.659,0.353-1.275,0.922-1.603l8.795-5.082c0.557-0.315,1.296-0.315,1.848,0l8.794,5.082c0.57,0.329,0.924,0.944,0.924,1.603 v10.15c0,0.659-0.354,1.275-0.924,1.604l-8.794,5.078C12.643,23.916,12.324,24,11.998,24z M19.099,13.993 c0-1.9-1.284-2.406-3.987-2.763c-2.731-0.361-3.009-0.548-3.009-1.187c0-0.528,0.235-1.233,2.258-1.233 c1.807,0,2.473,0.389,2.747,1.607c0.024,0.115,0.129,0.199,0.247,0.199h1.141c0.071,0,0.138-0.031,0.186-0.081 c0.048-0.054,0.074-0.123,0.067-0.196c-0.177-2.098-1.571-3.076-4.388-3.076c-2.508,0-4.004,1.058-4.004,2.833 c0,1.925,1.488,2.457,3.895,2.695c2.88,0.282,3.103,0.703,3.103,1.269c0,0.983-0.789,1.402-2.642,1.402 c-2.327,0-2.839-0.584-3.011-1.742c-0.02-0.124-0.126-0.215-0.253-0.215h-1.137c-0.141,0-0.254,0.112-0.254,0.253 c0,1.482,0.806,3.248,4.655,3.248C17.501,17.007,19.099,15.91,19.099,13.993z" fill="currentColor"/>
                        </svg>
                      )
                    },
                    {
                      name: 'Ruby',
                      icon: (
                        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none">
                          <path d="M20.156.083c3.033.525 3.893 2.598 3.829 4.77L24 4.822 22.635 22.71 4.89 23.926h.016C3.433 23.864.15 23.729 0 19.139l1.645-3 2.819 6.586.503 1.172 2.805-9.144-.03.007.016-.03 9.255 2.956-1.396-5.431-.99-3.9 8.82-.569-.615-.51L16.5 2.114 20.159.073l-.003.01zM0 19.089zM5.13 5.073c3.561-3.533 8.157-5.621 9.922-3.84 1.762 1.777-.105 6.105-3.673 9.636-3.563 3.532-8.103 5.734-9.864 3.957-1.766-1.777.045-6.217 3.612-9.75l.003-.003z" fill="currentColor"/>
                        </svg>
                      )
                    },
                    {
                      name: 'PHP',
                      icon: (
                        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none">
                          <path d="M7.01 10.207h-.944l-.515 2.648h.838c.556 0 .97-.105 1.242-.314.272-.21.455-.559.55-1.049.092-.47.05-.802-.124-.995-.175-.193-.523-.29-1.047-.29zM12 5.688C5.373 5.688 0 8.514 0 12s5.373 6.313 12 6.313S24 15.486 24 12c0-3.486-5.373-6.312-12-6.312zm-3.26 7.451c-.261.25-.575.438-.917.551-.336.108-.765.164-1.285.164H5.357l-.327 1.681H3.652l1.23-6.326h2.65c.797 0 1.378.209 1.744.628.366.418.476 1.002.33 1.752a2.836 2.836 0 0 1-.305.847c-.143.255-.33.49-.561.703zm4.024.715l.543-2.799c.063-.318.039-.536-.068-.651-.107-.116-.336-.174-.687-.174h-.813l-.69 3.624H9.667l1.23-6.326h1.378l-.422 2.169h1.13c.627 0 1.06.098 1.299.294.24.197.33.543.271 1.039l-.598 3.076h-1.391zm7.597-2.265a2.782 2.782 0 0 1-.305.847c-.143.255-.33.49-.561.703a2.44 2.44 0 0 1-.917.551c-.336.108-.765.164-1.286.164h-1.18l-.327 1.681h-1.378l1.23-6.326h2.649c.797 0 1.378.209 1.744.628.366.417.477 1.001.331 1.752zm2.595-1.403h-.838l-.515 2.648h.838c.555 0 .97-.105 1.242-.314.272-.21.455-.559.549-1.049.092-.47.05-.802-.124-.995-.175-.193-.522-.29-1.047-.29z" fill="currentColor"/>
                        </svg>
                      )
                    },
                    {
                      name: 'Go',
                      icon: (
                        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none">
                          <path d="M1.811 10.231c-.047 0-.058-.023-.035-.059l.246-.315c.023-.035.081-.058.128-.058h4.172c.046 0 .058.035.035.07l-.199.303c-.023.036-.082.07-.117.07zM.047 11.306c-.047 0-.059-.023-.035-.058l.245-.316c.024-.035.082-.058.129-.058h5.328c.047 0 .07.035.058.07l-.093.28c0 .047-.047.082-.082.082zm2.828 1.075c-.047 0-.059-.035-.035-.07l.163-.292c.023-.035.07-.07.117-.07h2.337c.047 0 .07.035.07.082l-.023.28c0 .047-.047.082-.082.082zm12.129-2.36c-.736.187-1.239.327-1.963.514-.176.046-.187.058-.34-.117-.174-.199-.303-.327-.548-.444-.737-.362-1.45-.257-2.115.175-.795.514-1.204 1.274-1.192 2.22.011.935.654 1.706 1.577 1.835.795.105 1.46-.175 1.987-.77.105-.13.198-.27.315-.434H10.47c-.245 0-.304-.152-.222-.35.152-.362.432-.97.596-1.274a.315.315 0 0 1 .292-.187h4.253c-.023.316-.023.631-.07.947a4.983 4.983 0 0 1-.958 2.29c-.841 1.11-1.94 1.8-3.33 1.986-1.145.152-2.209-.07-3.143-.77-.865-.655-1.356-1.52-1.484-2.595-.152-1.274.222-2.419.993-3.424.83-1.086 1.928-1.776 3.272-2.02 1.098-.2 2.15-.07 3.096.571.62.41 1.063.97 1.356 1.648.07.105.023.164-.117.2m3.868 6.461c-1.064-.024-2.034-.328-2.852-1.029a3.665 3.665 0 0 1-1.262-2.255c-.21-1.32.152-2.489.947-3.529.853-1.122 1.881-1.706 3.272-1.963 1.157-.211 2.267-.094 3.307.571.817.524 1.397 1.24 1.677 2.196.246.852.164 1.67-.152 2.501-.573 1.518-1.66 2.477-3.307 2.828-.549.117-1.11.164-1.659.164-.164 0-.328-.011-.493-.011zm2.372-3.306a2.213 2.213 0 0 0-.499-1.682c-.398-.386-.881-.538-1.427-.434a2.075 2.075 0 0 0-1.145.56c-.434.398-.676.898-.757 1.485-.105.758.128 1.451.768 1.869.573.375 1.192.315 1.777-.023.584-.338.951-.868 1.075-1.625.023-.117.035-.234.035-.351z" fill="currentColor"/>
                        </svg>
                      )
                    },
                    {
                      name: '.NET',
                      icon: (
                        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none">
                          <path d="M24 8.77h-2.468v7.565h-1.425V8.77h-2.462V7.53H24zm-6.852 7.565h-4.821V7.53h4.63v1.24h-3.205v2.494h2.953v1.234h-2.953v2.604h3.396zm-6.708 0H8.882L4.78 9.863a2.896 2.896 0 0 1-.258-.51h-.036c.032.189.048.592.048 1.21v5.772H3.157V7.53h1.659l3.965 6.32c.167.261.275.442.323.54h.024c-.04-.233-.06-.629-.06-1.185V7.529h1.372zm-8.703-.693a.868.868 0 0 1-.869.869.868.868 0 1 1 0-1.737c.48 0 .869.388.869.868z" fill="currentColor"/>
                        </svg>
                      )
                    }
                  ].map((sdk, idx) => (
                    <div
                      key={idx}
                      className="flex flex-col items-center gap-3 p-4 bg-white rounded-xl border border-neutral-200 hover:border-neutral-300 hover:shadow-md transition-all"
                    >
                      <div className="text-neutral-900">
                        {sdk.icon}
                      </div>
                      <span className="text-sm font-semibold text-neutral-900">{sdk.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>


            <div className="space-y-5">

              <div className="flex items-center gap-2 mb-4 overflow-x-auto">
                <button className="px-4 py-2 bg-neutral-900 text-white text-sm font-medium rounded-lg whitespace-nowrap">
                  Create Charge
                </button>
                <button className="px-4 py-2 bg-neutral-100 text-neutral-600 text-sm font-medium rounded-lg hover:bg-neutral-200 transition-colors whitespace-nowrap">
                  Retrieve Charge
                </button>
                <button className="px-4 py-2 bg-neutral-100 text-neutral-600 text-sm font-medium rounded-lg hover:bg-neutral-200 transition-colors whitespace-nowrap">
                  List Charges
                </button>
              </div>


              <div className="card p-0 bg-neutral-950 text-neutral-100 font-mono text-sm overflow-hidden shadow-2xl border-2 border-neutral-800">
                <div className="flex items-center justify-between px-5 py-3 border-b border-neutral-800 bg-black">
                  <div className="flex items-center gap-3">
                    <div className="flex gap-1.5">
                      <div className="w-3 h-3 rounded-full bg-red-500" />
                      <div className="w-3 h-3 rounded-full bg-yellow-500" />
                      <div className="w-3 h-3 rounded-full bg-emerald-500" />
                    </div>
                    <span className="text-neutral-400 text-xs font-medium">create_charge.py</span>
                  </div>
                  <button className="text-xs text-neutral-500 hover:text-neutral-300 transition-colors">
                    Copy
                  </button>
                </div>
                <div className="p-6 overflow-x-auto bg-neutral-950 max-h-[450px] overflow-y-auto">
                  <pre className="text-xs leading-relaxed">
                    <code className="text-neutral-200">
<span className="text-purple-400">import</span> <span className="text-emerald-400">requests</span>{'\n'}
<span className="text-purple-400">from</span> <span className="text-emerald-400">decimal</span> <span className="text-purple-400">import</span> <span className="text-emerald-400">Decimal</span>{'\n'}
{'\n'}
<span className="text-neutral-500"># Initialize Ivy API client</span>{'\n'}
<span className="text-blue-400">BASE_URL</span> = <span className="text-amber-300">"https://api.ivy-payments.com"</span>{'\n'}
<span className="text-blue-400">API_KEY</span> = <span className="text-amber-300">"sk_live_..."</span>  <span className="text-neutral-500"># Your secret key</span>{'\n'}
{'\n'}
<span className="text-blue-400">headers</span> = {'{'}{'\n'}
{'    '}<span className="text-amber-300">"Authorization"</span>: <span className="text-amber-300">"X-API-KEY": API_KEY,</span>,{'\n'}
{'    '}<span className="text-amber-300">"Content-Type"</span>: <span className="text-amber-300">"application/json"</span>,{'\n'}
{'    '}<span className="text-amber-300">"Idempotency-Key"</span>: <span className="text-amber-300">"unique_id_123"</span>{'\n'}
{'}'}{'\n'}
{'\n'}
<span className="text-neutral-500"># Create a new charge</span>{'\n'}
<span className="text-blue-400">charge_data</span> = {'{'}{'\n'}
{'    '}<span className="text-amber-300">"amount"</span>: <span className="text-blue-400">Decimal</span>(<span className="text-amber-300">"5000.00"</span>),{'\n'}
{'    '}<span className="text-amber-300">"currency"</span>: <span className="text-amber-300">"NGN"</span>,{'\n'}
{'    '}<span className="text-amber-300">"description"</span>: <span className="text-amber-300">"Premium subscription - Annual"</span>,{'\n'}
{'    '}<span className="text-amber-300">"customer"</span>: {'{'}{'\n'}
{'        '}<span className="text-amber-300">"email"</span>: <span className="text-amber-300">"customer@example.com"</span>,{'\n'}
{'        '}<span className="text-amber-300">"name"</span>: <span className="text-amber-300">"Frank Ocean"</span>{'\n'}
{'    '}{'}'},{'\n'}
{'    '}<span className="text-amber-300">"metadata"</span>: {'{'}{'\n'}
{'        '}<span className="text-amber-300">"order_id"</span>: <span className="text-amber-300">"ord_789xyz"</span>,{'\n'}
{'        '}<span className="text-amber-300">"plan"</span>: <span className="text-amber-300">"premium_annual"</span>{'\n'}
{'    '}{'}'}{'\n'}
{'}'}{'\n'}
{'\n'}
<span className="text-neutral-500"># Send request to create charge</span>{'\n'}
<span className="text-blue-400">response</span> = requests.<span className="text-blue-400">post</span>({'\n'}
{'    '}<span className="text-amber-300">f"{'{'}BASE_URL{'}'}/v1/charges/"</span>,{'\n'}
{'    '}json=charge_data,{'\n'}
{'    '}headers=headers{'\n'}
){'\n'}
{'\n'}
<span className="text-purple-400">if</span> response.status_code == <span className="text-blue-400">201</span>:{'\n'}
{'    '}<span className="text-blue-400">charge</span> = response.<span className="text-blue-400">json</span>(){'\n'}
{'    '}<span className="text-purple-400">print</span>(<span className="text-amber-300">f" Charge created: {'{'}charge['id']{'}'}"</span>){'\n'}
{'    '}<span className="text-purple-400">print</span>(<span className="text-amber-300">f" Status: {'{'}charge['status']{'}'}"</span>){'\n'}
{'    '}<span className="text-purple-400">print</span>(<span className="text-amber-300">f" Amount: ₦{'{'}charge['amount']{'}'}"</span>){'\n'}
<span className="text-purple-400">else</span>:{'\n'}
{'    '}<span className="text-purple-400">print</span>(<span className="text-amber-300">f"Error: {'{'}response.status_code{'}'}"</span>){'\n'}
{'    '}<span className="text-purple-400">print</span>(response.<span className="text-blue-400">json</span>()){'\n'}
{'\n'}
<span className="text-neutral-500"># Expected output:</span>{'\n'}
<span className="text-neutral-500">#  Charge created: ch_1AbCdEfGhIjK</span>{'\n'}
<span className="text-neutral-500">#   Status: succeeded</span>{'\n'}
<span className="text-neutral-500">#   Amount: ₦5000.00</span>
                    </code>
                  </pre>
                </div>
              </div>


              <div className="card p-0 bg-neutral-950 border-2 border-neutral-800 overflow-hidden shadow-xl">
                <div className="px-6 py-3 border-b border-neutral-800 bg-neutral-900/50 flex items-center justify-between">
                  <span className="text-neutral-300 text-xs font-semibold">Response - 201 Created</span>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-xs font-medium rounded">JSON</span>
                    <button className="text-xs text-neutral-500 hover:text-neutral-300 transition-colors">
                      Copy
                    </button>
                  </div>
                </div>
                <div className="p-6 overflow-x-auto bg-neutral-950">
                  <pre className="text-xs font-mono leading-loose">
                    <code className="text-neutral-200">
{'{'}{'\n'}
{'  '}<span className="text-amber-300">"id"</span>: <span className="text-blue-400">"ch_1AbCdEfGhIjK"</span>,{'\n'}
{'  '}<span className="text-amber-300">"object"</span>: <span className="text-blue-400">"charge"</span>,{'\n'}
{'  '}<span className="text-amber-300">"amount"</span>: <span className="text-blue-400">"5000.00"</span>,{'\n'}
{'  '}<span className="text-amber-300">"currency"</span>: <span className="text-blue-400">"NGN"</span>,{'\n'}
{'  '}<span className="text-amber-300">"status"</span>: <span className="text-emerald-400">"succeeded"</span>,{'\n'}
{'  '}<span className="text-amber-300">"description"</span>: <span className="text-blue-400">"Premium subscription - Annual"</span>,{'\n'}
{'  '}<span className="text-amber-300">"customer"</span>: {'{'}{'\n'}
{'    '}<span className="text-amber-300">"email"</span>: <span className="text-blue-400">"customer@example.com"</span>,{'\n'}
{'    '}<span className="text-amber-300">"name"</span>: <span className="text-blue-400">"Frank Ocean"</span>{'\n'}
{'  '}{'}'},{'\n'}
{'  '}<span className="text-amber-300">"created_at"</span>: <span className="text-blue-400">"2025-11-07T10:30:00Z"</span>,{'\n'}
{'  '}<span className="text-amber-300">"metadata"</span>: {'{'}{'\n'}
{'    '}<span className="text-amber-300">"order_id"</span>: <span className="text-blue-400">"ord_789xyz"</span>,{'\n'}
{'    '}<span className="text-amber-300">"plan"</span>: <span className="text-blue-400">"premium_annual"</span>{'\n'}
{'  '}{'}'}{'\n'}
{'}'}
                    </code>
                  </pre>
                </div>
              </div>


              <div className="bg-neutral-100 rounded-xl p-6 border border-neutral-200">
                <h4 className="font-semibold text-neutral-900 mb-4 text-sm">Quick Reference</h4>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="text-neutral-600">Base URL</span>
                    <code className="px-2 py-1 bg-white rounded text-neutral-900 font-mono text-xs">https://api.ivy-payments.com</code>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-neutral-600">Authentication</span>
                    <code className="px-2 py-1 bg-white rounded text-neutral-900 font-mono text-xs">Bearer Token</code>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-neutral-600">Rate Limit</span>
                    <code className="px-2 py-1 bg-white rounded text-neutral-900 font-mono text-xs">1000 req/min</code>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>


      <section id="pricing" className="py-32 px-6 bg-neutral-50">
        <div className="max-w-7xl mx-auto">

          <div className="text-center mb-20">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-full text-sm font-medium text-neutral-700 mb-6 border border-neutral-200 shadow-sm">
              <svg className="w-4 h-4 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Simple, transparent pricing</span>
            </div>
            <h2 className="text-5xl md:text-6xl font-bold tracking-tight mb-6">
              Pricing that scales with you
            </h2>
            <p className="text-xl text-neutral-600 max-w-3xl mx-auto">
              No hidden fees, no setup costs, no monthly charges. Pay only for successful transactions.
            </p>
          </div>


          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">

            <div className="bg-white rounded-2xl border-2 border-neutral-200 p-8 hover:shadow-xl transition-all">
              <div className="mb-6">
                <h3 className="text-lg font-semibold tracking-tight text-neutral-900 mb-2">Starter</h3>
                <p className="text-sm text-neutral-600">Perfect for small businesses and startups</p>
              </div>
              <div className="mb-8">
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-bold text-neutral-900 tabular-nums lining-nums">2.9%</span>
                  <span className="text-xl text-neutral-600 tabular-nums lining-nums">+ $0.30</span>
                </div>
                <p className="text-sm text-neutral-600 mt-2">per successful transaction</p>
              </div>
              <Link
                to="/register"
                className="block w-full py-3 px-6 bg-neutral-100 hover:bg-neutral-200 text-neutral-900 font-semibold rounded-xl transition-all text-center mb-8"
              >
                Get started
              </Link>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium text-neutral-900">Accept all major cards</p>
                    <p className="text-sm text-neutral-600">Visa, Mastercard, Amex, Discover</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium text-neutral-900">Dashboard & reporting</p>
                    <p className="text-sm text-neutral-600">Real-time analytics and insights</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium text-neutral-900">API access</p>
                    <p className="text-sm text-neutral-600">Full REST API with webhooks</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium text-neutral-900">Email support</p>
                    <p className="text-sm text-neutral-600">24-hour response time</p>
                  </div>
                </div>
              </div>
            </div>


            <div className="bg-neutral-900 text-white rounded-2xl border-2 border-neutral-900 p-8 shadow-2xl transform scale-105 relative">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-emerald-500 text-white text-xs font-bold rounded-full uppercase tracking-wide">
                Most Popular
              </div>
              <div className="mb-6">
                <h3 className="text-lg font-semibold tracking-tight mb-2">Growth</h3>
                <p className="text-sm text-neutral-400">For growing businesses processing volume</p>
              </div>
              <div className="mb-8">
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-bold tabular-nums lining-nums">2.5%</span>
                  <span className="text-xl text-neutral-400 tabular-nums lining-nums">+ $0.25</span>
                </div>
                <p className="text-sm text-neutral-400 mt-2">per successful transaction</p>
              </div>
              <Link
                to="/register"
                className="block w-full py-3 px-6 bg-white hover:bg-neutral-100 text-neutral-900 font-semibold rounded-xl transition-all text-center mb-8"
              >
                Get started
              </Link>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium">Everything in Starter</p>
                    <p className="text-sm text-neutral-400">All basic features included</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium">Priority support</p>
                    <p className="text-sm text-neutral-400">4-hour response time</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium">Multi-currency support</p>
                    <p className="text-sm text-neutral-400">Accept 135+ currencies</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium">Advanced fraud detection</p>
                    <p className="text-sm text-neutral-400">Machine learning protection</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium">Custom settlement schedule</p>
                    <p className="text-sm text-neutral-400">Daily or weekly payouts</p>
                  </div>
                </div>
              </div>
            </div>


            <div className="bg-white rounded-2xl border-2 border-neutral-200 p-8 hover:shadow-xl transition-all">
              <div className="mb-6">
                <h3 className="text-lg font-semibold tracking-tight text-neutral-900 mb-2">Enterprise</h3>
                <p className="text-sm text-neutral-600">For high-volume businesses with custom needs</p>
              </div>
              <div className="mb-8">
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-bold text-neutral-900 tabular-nums lining-nums">Custom</span>
                </div>
                <p className="text-sm text-neutral-600 mt-2">Volume-based pricing available</p>
              </div>
              <button className="block w-full py-3 px-6 bg-neutral-900 hover:bg-neutral-800 text-white font-semibold rounded-xl transition-all text-center mb-8">
                Contact sales
              </button>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium text-neutral-900">Everything in Growth</p>
                    <p className="text-sm text-neutral-600">All premium features</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium text-neutral-900">Dedicated account manager</p>
                    <p className="text-sm text-neutral-600">Personalized support team</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium text-neutral-900">99.99% uptime SLA</p>
                    <p className="text-sm text-neutral-600">Guaranteed availability</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium text-neutral-900">Custom integrations</p>
                    <p className="text-sm text-neutral-600">Tailored to your needs</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="font-medium text-neutral-900">Advanced compliance</p>
                    <p className="text-sm text-neutral-600">PCI DSS Level 1, SOC 2</p>
                  </div>
                </div>
              </div>
            </div>
          </div>


          <div className="bg-white rounded-2xl border border-neutral-200 p-10">
            <h3 className="text-2xl font-bold text-neutral-900 mb-8 text-center">What's included in all plans</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-14 h-14 bg-neutral-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-7 h-7 text-neutral-900" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <h4 className="font-semibold tracking-tight text-neutral-900 mb-2">Bank-level security</h4>
                <p className="text-sm text-neutral-600">End-to-end encryption and PCI DSS compliance</p>
              </div>
              <div className="text-center">
                <div className="w-14 h-14 bg-neutral-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-7 h-7 text-neutral-900" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h4 className="font-semibold tracking-tight text-neutral-900 mb-2">Instant activation</h4>
                <p className="text-sm text-neutral-600">Start accepting payments in minutes, not days</p>
              </div>
              <div className="text-center">
                <div className="w-14 h-14 bg-neutral-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-7 h-7 text-neutral-900" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h4 className="font-semibold tracking-tight text-neutral-900 mb-2">No hidden fees</h4>
                <p className="text-sm text-neutral-600">Transparent pricing with no surprise charges</p>
              </div>
            </div>
          </div>
        </div>
      </section>


      <section className="py-32 px-6 relative overflow-hidden bg-neutral-900">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_50%,rgba(255,255,255,0.08),transparent)]" />
        <div className="relative max-w-4xl mx-auto text-center text-white">
          <h2 className="text-5xl md:text-6xl font-bold tracking-tight mb-6">
            Ready to scale your payments?
          </h2>
          <p className="text-xl text-neutral-400 mb-12 max-w-2xl mx-auto leading-relaxed tabular-nums lining-nums">
            Join 12,500+ businesses that trust Ivy to power their financial infrastructure
          </p>
          <div className="flex flex-wrap items-center justify-center gap-5">
            <Link to="/register" className="btn bg-white text-neutral-900 hover:bg-neutral-100 text-lg px-12 py-5 font-bold shadow-2xl">
              Create your account
            </Link>
            <button className="btn bg-transparent border-2 border-white/30 text-white hover:bg-white/10 text-lg px-12 py-5 font-semibold">
              Contact sales
            </button>
          </div>
        </div>
      </section>


      <footer id="support" className="py-20 px-6 bg-white border-t border-neutral-200">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-12 mb-16">
            <div className="col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 bg-neutral-900 rounded-xl flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707" />
                  </svg>
                </div>
                <span className="text-2xl font-semibold">Ivy</span>
              </div>
              <p className="text-neutral-600 text-sm leading-relaxed max-w-sm">
                Financial infrastructure for the internet. Built for developers, trusted by enterprises.
              </p>
            </div>
            {[
              { title: 'Product', links: ['Features', 'Pricing', 'API', 'Documentation', 'Changelog'] },
              { title: 'Company', links: ['About', 'Blog', 'Careers', 'Press Kit', 'Partners'] },
              { title: 'Legal', links: ['Privacy', 'Terms', 'Security', 'Compliance', 'Licenses'] }
            ].map((col, idx) => (
              <div key={idx}>
                <h3 className="font-semibold tracking-tight mb-4 text-sm text-neutral-900">{col.title}</h3>
                <ul className="space-y-3">
                  {col.links.map((link, i) => (
                    <li key={i}>
                      <a href="#" className="text-sm text-neutral-600 hover:text-neutral-900 transition-colors">
                        {link}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <div className="pt-8 border-t border-neutral-200 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-neutral-600">
              © {new Date().getFullYear()} Ivy Technologies, Inc. All rights reserved.
            </p>
            <div className="flex items-center gap-6 text-sm">
              <a href="#" className="text-neutral-600 hover:text-neutral-900 transition-colors">Status</a>
              <a href="#" className="text-neutral-600 hover:text-neutral-900 transition-colors">Support</a>
              <a href="#" className="text-neutral-600 hover:text-neutral-900 transition-colors">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}



