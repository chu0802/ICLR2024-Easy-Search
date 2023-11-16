import openreview
import os
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from typing import List, Union, Optional


@dataclass
class Review:
    rating: Union[int, float] = None
    confidence: Union[int, float] = None
    
    def __add__(self, other):
        if other == 0:
            return Review(self.rating, self.confidence)
        assert isinstance(other, Review)
        return Review(self.rating + other.rating, self.confidence + other.confidence)
    
    def __truediv__(self, integer):
        return Review(self.rating / integer, self.confidence / integer)

    def __radd__(self, other):
        return self.__add__(other)
    
    @classmethod
    def from_dict(cls, json_dict):
        return cls(**json_dict)


@dataclass
class Paper:
    id: str
    number: int
    title: str
    forum_url: str
    pdf_url: str
    reviews: List[Review]
    avg_score: Optional[float] = 0
    avg_conf: Optional[float] = 0
    
    def __post_init__(self):
        self.avg_score = self.get_score().rating
        self.avg_conf = self.get_score().confidence

    @classmethod
    def from_note(cls, note):
        dic = note.__dict__
        return cls(
            id=dic["id"],
            number=dic["number"],
            title=dic["content"]['title']['value'],
            forum_url=f"https://openreview.net/forum?id={dic['forum']}",
            pdf_url=f"https://openreview.net{dic['content']['pdf']['value']}",
            reviews=[
                Review(
                    rating=int(review["content"]["rating"]["value"][0]),
                    confidence=int(review["content"]["confidence"]["value"][0]),
                ) 
                for review in dic["details"]['directReplies']
                if "rating" in review["content"] and "confidence" in review["content"]
            ]
        )

    @classmethod
    def from_dict(cls, json_dict):
        json_dict["reviews"] = [Review.from_dict(dict) for dict in json_dict["reviews"]]
        return cls(**json_dict)

    def get_score(self):
        if len(self.reviews) == 0:
            return Review(-1, -1)
        return sum(self.reviews) / len(self.reviews)


class OpenReviewClient:
    def __init__(self, cache_dir="./.cache"):
        self.client = openreview.api.OpenReviewClient(
            baseurl="https://api2.openreview.net",
            username=os.environ.get("OPENREVIEW_USERNAME", None),
            password=os.environ.get("OPENREVIEW_PASSWORD", None)
        )
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)

    def get_conference_id(self, conf, year):
        venues = self.client.get_group(id='venues').members
        return list(filter(lambda venue: year in venue and conf in venue and "conference" in venue.lower(), venues))[0]
    
    def load_papers_from_json(self, path):
        with path.open("r") as f:
            papers = [Paper.from_dict(json_dict) for json_dict in json.load(f)]
        return papers
    
    def load_papers_online(self, conference_id):
        group = self.client.get_group(conference_id)
        submission_name = group.content['submission_name']['value']
        
        return [
            Paper.from_note(paper)
            for paper in self.client.get_all_notes(invitation=f'{conference_id}/-/{submission_name}', details='directReplies')
        ]
        
    def save_papers_to_json(self, papers, path):
        with path.open("w") as f:
            json.dump([asdict(paper) for paper in papers], f, indent=4)

    def get_papers(self, conf, year):
        conference_id = self.get_conference_id(conf, year)
        cache_path = self.cache_dir / f"{conference_id}.json".replace("/", "_")
        if cache_path.exists():
            papers = self.load_papers_from_json(cache_path)
        else:
            papers = self.load_papers_online(conference_id)
            self.save_papers_to_json(papers, cache_path)
                
        return papers