# Partner Selection System - User Guide

## Overview
The partner selection system has been completely redesigned from dropdown menus to an interactive profile card system with detailed information displays.

## How to Use

### Selecting a Celebrity Co-Founder
1. Click the **"Celebrity Co-Founder"** button in the setup panel
2. A modal will open showing a 2-column grid of 8 celebrity partner cards
3. Each card displays:
   - Avatar image (resembles the person)
   - Name
   - Core Ability (e.g., "Moonshot Architect")
   - Domain (e.g., "Tech")
4. Click any card to view the full profile

### Viewing a Partner Profile
When you click a partner card, a detailed profile modal opens showing:
- **Large avatar image** - distinctive avatar resembling the person
- **Core Ability** - headline describing their key strength (e.g., "Cult Builder")
- **Domain** - their area of expertise (e.g., "Brand", "Tech", "Finance")
- **Description** - detailed summary of their contribution style
- **Key Stats** - top 4 statistics from their 8-stat profile (e.g., Growth, Brand, Product, Tech, Ops, Finance, Innovation, Execution)
- **Strengths** - top 3 specializations with human-readable descriptions (e.g., "Growth: Strong ability to scale and grow user base")

### Selecting the Partner
Click the **"Select This Partner"** button in the profile modal to confirm your choice. The modal will close and the partner's name will appear in the setup panel.

### Selecting an Academic Specialist
Repeat the same process for the **"Academic Specialist"** button to choose from 6 professors with research/academic expertise.

### Available Partners

#### Celebrity Co-Founders (8 total)
- **Taylor Swift** - Cult Builder (Brand)
- **Elon Musk** - Moonshot Architect (Tech)
- **Steve Jobs** - Product Perfectionist (Product)
- **MrBeast** - Viral Growth Hacker (Growth)
- **Warren Buffett** - Capital Allocator (Finance)
- **Jeff Bezos** - Scale Engine (Operations)
- **Albert Einstein** - Deep Thinker (R&D)
- **Lionel Messi** - Team Synergy (Team)

#### Academic Specialists (6 total)
- **Oriol Rius** - Tech Architect (Technology)
- **Esteve Almirall** - Innovation Strategist (Innovation)
- **Jose A. Rodriguez-Serrano** - ML Strategist (AI / ML)
- **Ruben Coca** - Industry Analyst (Analytics)
- **Jordi Nin** - Research Scientist (Data Science / AI)
- **Maja Tampe** - Governance Architect (Sustainability)

## Partnership Synergies
Certain combinations of celebrity + professor unlock special synergies that boost your startup's capabilities:
- **AI Frontier** - Elon Musk + Jose A. Rodriguez-Serrano
- **Full Stack** - Elon Musk + Oriol Rius
- **Deep Research** - Albert Einstein + Jordi Nin
- **Quant Finance** - Warren Buffett + Ruben Coca
- **Data Empire** - Jeff Bezos + Ruben Coca
- **Responsible Scale** - Jeff Bezos + Maja Tampe
- **Cult of Impact** - Taylor Swift + Maja Tampe
- **Product x Innovation** - Steve Jobs + Esteve Almirall
- **Innovation Lab** - MrBeast + Esteve Almirall

When you unlock a synergy, you'll see it listed under "Synergy" in the game log after generating your setup.

## Implementation Details

### Avatar System
Each partner has a unique avatar image generated via the DiceBear API, providing a visually distinct representation for each person.

### Stat Display
Partners are rated on 8 key dimensions:
- **Growth** - Scaling ability
- **Brand** - Brand building
- **Product** - Product development
- **Tech** - Technical expertise
- **Ops** - Operational excellence
- **Finance** - Financial acumen
- **Innovation** - Innovative thinking
- **Execution** - Delivery capability

Stats are visualized as numerical scores (0-10) in the detailed profile view.

### User Experience Flow
1. Setup → Select Founder → Select Celebrity Partner → Select Professor Partner → Generate Setup
2. At each partner selection step, click buttons to open interactive modals
3. Browse cards → View details → Select → Confirm
4. Both partners lock in before setup generation

## Technical Notes
- Profile modals include all partner data from backend API
- Avatars are sourced from DiceBear Avataaars service
- Stat descriptions and synergy bonuses calculated server-side
- All partner selections validated before setup generation
