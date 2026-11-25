"use client";
import SharedRecommendations from '../../frontend/src/recommendations/Recommendations';
import {readRecommendations,recommendationCommand} from '../app/workspace/recommendation-actions';
import type {Department} from '../lib/workspace-contracts';
export default function Recommendations({businessId,role='ceo',boardroom=false}:{businessId:string;role?:Department;boardroom?:boolean}){return <SharedRecommendations key={`${businessId}:${role}:${boardroom}`} businessId={businessId} role={role} boardroom={boardroom} readRecommendations={readRecommendations} recommendationCommand={recommendationCommand}/>}
