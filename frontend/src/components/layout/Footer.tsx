/**
 * Footer Component
 *
 * Site footer with property info and useful links.
 */

export interface FooterProps {
  /** Show minimal footer (just copyright) */
  minimal?: boolean
}

export function Footer({ minimal = false }: FooterProps) {
  const currentYear = new Date().getFullYear()

  if (minimal) {
    return (
      <footer className="footer footer-minimal">
        <p className="footer-copyright">
          © {currentYear} Summerhouse. All rights reserved.
        </p>

        <style jsx>{`
          .footer-minimal {
            padding: 1rem;
            text-align: center;
            font-size: 0.75rem;
            color: #6b7280;
            background: #f9fafb;
            border-top: 1px solid #e5e7eb;
          }

          .footer-copyright {
            margin: 0;
          }
        `}</style>
      </footer>
    )
  }

  return (
    <footer className="footer">
      <div className="footer-content">
        {/* Property Info */}
        <div className="footer-section">
          <h3 className="footer-heading">☀️ Summerhouse</h3>
          <p className="footer-description">
            Your vacation home in the Costa Blanca region. Experience the best of
            Spanish sunshine, beaches, and culture in Quesada, Alicante.
          </p>
        </div>

        {/* Quick Links */}
        <div className="footer-section">
          <h4 className="footer-subheading">Quick Links</h4>
          <ul className="footer-links">
            <li>
              <a href="#availability">Check Availability</a>
            </li>
            <li>
              <a href="#property">Property Details</a>
            </li>
            <li>
              <a href="#area">Explore the Area</a>
            </li>
          </ul>
        </div>

        {/* Contact */}
        <div className="footer-section">
          <h4 className="footer-subheading">Contact</h4>
          <ul className="footer-links">
            <li>Chat with our AI assistant 24/7</li>
            <li>📍 Quesada, Alicante, Spain</li>
          </ul>
        </div>
      </div>

      <div className="footer-bottom">
        <p className="footer-copyright">
          © {currentYear} Summerhouse. All rights reserved.
        </p>
        <div className="footer-legal">
          <a href="/privacy">Privacy Policy</a>
          <a href="/terms">Terms of Service</a>
        </div>
      </div>

      <style jsx>{`
        .footer {
          background: #1f2937;
          color: #e5e7eb;
          padding: 3rem 1rem 1.5rem;
        }

        .footer-content {
          max-width: 1200px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 2rem;
        }

        .footer-section {
          min-width: 0;
        }

        .footer-heading {
          font-size: 1.25rem;
          font-weight: 700;
          margin: 0 0 0.75rem;
          color: white;
        }

        .footer-subheading {
          font-size: 0.875rem;
          font-weight: 600;
          margin: 0 0 0.5rem;
          color: white;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .footer-description {
          font-size: 0.875rem;
          line-height: 1.6;
          margin: 0;
          color: #9ca3af;
        }

        .footer-links {
          list-style: none;
          margin: 0;
          padding: 0;
        }

        .footer-links li {
          font-size: 0.875rem;
          margin-bottom: 0.375rem;
          color: #9ca3af;
        }

        .footer-links a {
          color: #9ca3af;
          text-decoration: none;
          transition: color 0.2s;
        }

        .footer-links a:hover {
          color: white;
        }

        .footer-bottom {
          max-width: 1200px;
          margin: 2rem auto 0;
          padding-top: 1.5rem;
          border-top: 1px solid #374151;
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 1rem;
        }

        .footer-copyright {
          margin: 0;
          font-size: 0.75rem;
          color: #6b7280;
        }

        .footer-legal {
          display: flex;
          gap: 1.5rem;
        }

        .footer-legal a {
          font-size: 0.75rem;
          color: #6b7280;
          text-decoration: none;
          transition: color 0.2s;
        }

        .footer-legal a:hover {
          color: #9ca3af;
        }

        @media (max-width: 640px) {
          .footer-bottom {
            flex-direction: column;
            text-align: center;
          }
        }
      `}</style>
    </footer>
  )
}

export default Footer
