# Sponsorship Setup Guide

This document explains the sponsorship configuration added to the Routing Table API project.

## What Was Added

### 1. GitHub Funding Configuration (`.github/FUNDING.yml`)

Created the GitHub funding configuration file that enables the **"Sponsor"** button to appear in the repository header. This file supports multiple sponsorship platforms:

- **GitHub Sponsors** (recommended)
- Patreon
- Open Collective
- Ko-fi
- Buy Me a Coffee
- Custom URLs

**Current Status:** Template created with all options commented out. Uncomment and configure as needed.

### 2. Enhanced README.md

#### Badge Added
Added a pink sponsorship badge to the top of README with link to GitHub Sponsors:
```markdown
[![Sponsor](https://img.shields.io/badge/Sponsor-??-pink?logo=github)](https://github.com/sponsors/weekmo)
```

#### Improved Sponsor Section
Completely rewrote the Sponsor section with:
- **Clear call-to-action** for GitHub Sponsors
- **Sponsor tier structure** ($5, $25, $100, $500/month)
- **Setup instructions** for maintainers
- **Alternative support options** (star, contribute, share, donate)
- **Commercial support information** for enterprises
- **Sponsor recognition section** (placeholder for listing sponsors)
- **Contact information** for corporate sponsorship

## How to Activate GitHub Sponsors

### For Maintainers (weekmo)

1. **Sign up for GitHub Sponsors:**
   - Go to https://github.com/sponsors
   - Click "Join the waitlist" or "Set up GitHub Sponsors"
   - Complete the application (requires Stripe Connect account)
   - Set up sponsor tiers with benefits

2. **Configure sponsor tiers** (suggested):
   - **$5/month** - Individual Supporter
     - Name listed in README
     - Sponsor badge on profile
   
   - **$25/month** - Professional User
     - Everything in previous tier
     - Logo + link in README
     - Priority issue responses
   
   - **$100/month** - Organization Sponsor
     - Everything in previous tiers
     - Prominent logo placement
     - Monthly progress updates
     - Influence on roadmap
   
   - **$500/month** - Enterprise Sponsor
     - Everything in previous tiers
     - Custom feature development
     - SLA support agreement
     - Direct communication channel

3. **Update `.github/FUNDING.yml`:**
   ```yaml
   # Uncomment this line:
   github: weekmo
   ```

4. **The sponsor button appears automatically** once GitHub approves your application

### For Alternative Platforms

If you prefer platforms other than GitHub Sponsors, update `.github/FUNDING.yml`:

**Example - Buy Me a Coffee:**
```yaml
buy_me_a_coffee: weekmo
```

**Example - Multiple platforms:**
```yaml
github: weekmo
ko_fi: weekmo
custom: ['https://paypal.me/weekmo']
```

## Benefits of Sponsorship

### For the Project
- **Sustainable maintenance** - Fund time for bug fixes and updates
- **Faster feature development** - Prioritize requested features
- **Better documentation** - Resources for comprehensive guides
- **Community growth** - Support for events, swag, etc.

### For Sponsors
- **Support open source** - Give back to tools you use
- **Influence development** - Vote on features and priorities
- **Recognition** - Logo/name in README and releases
- **Priority support** - Faster responses to issues
- **Good publicity** - Show your company supports OSS

## Marketing the Sponsorship

Once activated, promote sponsorship through:

1. **Repository README** ? (Already added)
2. **Repository "Sponsor" button** ? (Configured)
3. **Release notes** - Thank sponsors in changelog
4. **Social media** - Tweet/post about becoming a sponsor
5. **Documentation site** - Add sponsor page if you have docs
6. **Issue/PR templates** - Mention sponsorship option
7. **Blog posts** - Write about project needs and goals

## Tracking Sponsors

GitHub Sponsors provides:
- Dashboard with revenue and sponsor count
- Email notifications for new sponsors
- Export of sponsor data
- Analytics on tier popularity

## Legal and Tax Considerations

- GitHub Sponsors uses Stripe Connect for payments
- Fees: GitHub takes 0% (Stripe takes ~3% payment processing)
- Tax forms required (W-9 for US, W-8 for international)
- Sponsorship income may be taxable - consult tax advisor
- GPL-3.0 license remains - sponsorship doesn't change access

## FAQs

**Q: Does sponsorship affect the GPL-3.0 license?**
A: No. The project remains open source and free to use.

**Q: What if I can't afford to sponsor?**
A: No problem! Contributing code, docs, or bug reports is equally valuable.

**Q: Can I sponsor anonymously?**
A: Yes, GitHub Sponsors allows private sponsorships.

**Q: What happens if I stop sponsoring?**
A: You can cancel anytime. Access to the project doesn't change.

**Q: Can my company get an invoice?**
A: Yes, GitHub provides invoices for corporate sponsors.

## Resources

- [GitHub Sponsors Documentation](https://docs.github.com/en/sponsors)
- [GitHub Sponsors for Organizations](https://github.com/sponsors)
- [Stripe Connect](https://stripe.com/connect)
- [Funding.yml Specification](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/displaying-a-supporter-button-in-your-repository)

## Next Steps

1. ? FUNDING.yml created
2. ? README.md updated with sponsor section
3. ? **Next:** Sign up for GitHub Sponsors
4. ? **Next:** Uncomment `github: weekmo` in FUNDING.yml
5. ? **Next:** Configure sponsor tiers
6. ? **Next:** Promote to potential sponsors

---

**Questions?** Open an issue or contact the maintainer.
