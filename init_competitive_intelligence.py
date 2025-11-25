#!/usr/bin/env python3
"""
Script para inicializar el sistema de Competitive Intelligence
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🚀 Inicializando Sistema de Competitive Intelligence...")
    print("=" * 60)
    
    try:
        # 1. Inicializar sistema de suscripciones
        print("📊 Inicializando sistema de suscripciones...")
        from subscription_system import SubscriptionSystem
        sub_system = SubscriptionSystem()
        print("✅ Sistema de suscripciones inicializado")
        
        # 2. Inicializar sistema de competitive intelligence
        print("🕵️ Inicializando sistema de competitive intelligence...")
        from competitive_intelligence_system import CompetitiveIntelligenceSystem
        ci_system = CompetitiveIntelligenceSystem()
        print("✅ Sistema de competitive intelligence inicializado")
        
        # 3. Verificar que los planes tengan límites de competidores
        print("🔍 Verificando planes de suscripciones...")
        plans = sub_system.get_all_plans()
        for plan in plans:
            print(f"   📋 Plan: {plan['display_name']} - Límite competidores: {plan.get('max_competitors', 'No definido')}")
        
        print("\n🎉 ¡Sistema de Competitive Intelligence inicializado correctamente!")
        print("\n📋 Funcionalidades disponibles:")
        print("   • Monitoreo de competidores")
        print("   • Análisis de sentimiento automático")
        print("   • Alertas en tiempo real")
        print("   • Analytics competitivos")
        print("   • Límites por plan de suscripción")
        
        print("\n💰 Planes disponibles:")
        print("   • Gratuito: 1 competidor")
        print("   • Premium ($29/mes): 5 competidores")
        print("   • Enterprise ($99/mes): 20 competidores")
        
        print("\n🚀 ¡Listo para generar ingresos!")
        
    except Exception as e:
        print(f"❌ Error inicializando el sistema: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

















